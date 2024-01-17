from playwright.sync_api import sync_playwright, Error, TimeoutError
from celery import shared_task, states, group
from celery.result import AsyncResult
import json
import urllib
import logging
from .database import db, HotelSearchKeys
from celery.exceptions import MaxRetriesExceededError, Ignore
import traceback
import re
import httpx

site_url = "https://www.tripadvisor.com/"
search_url = "https://www.tripadvisor.com/Search?q="

settings_file = "settings.json"
browser_url = None

logger = logging.getLogger(__name__)

with open(settings_file) as json_file:
    settings = json.load(json_file)
    user_agent = settings['user_agent']
    proxies = None if settings['proxies'] == "" else settings['proxies']
    username = None if settings['username'] == "" else settings['username']
    password = None if settings['password'] == "" else settings['password']
    wss_host = None if settings['wss_host'] == "" else settings['wss_host']
    depth_level = settings['depth_level']
    if username and password and wss_host:
        browser_url = f"wss://{settings['username']}:{settings['password']}@{settings['wss_host']}"

#
# UTILITY FUNCTIONS
#
def start_scraping_async(search_text):
    chain = (check_db_for_link.s(search_text) | 
             get_hotel_link.s().set(retry=True) |
             save_hotel_link.s() |
             generate_paginated_hotels.s()
             ).apply_async()
    return chain.id

def getHotelListPage(page, context, search_text):
    print(f"Searching for {search_text} on {page.url}")
    top_result = page.locator(
        "div[data-widget-type='TOP_RESULT'] div.result-title").first
    with context.expect_page() as new_page_info:
        top_result.click()
        new_page = new_page_info.value

    new_page.wait_for_load_state()
    hotel_link = new_page.locator(
        "div[data-test-target='nav-links'] a").filter(has_text="Hotels")
    return hotel_link.get_attribute("href")

#
# CELERY TASKS
#
@shared_task(name='check database for link')
def check_db_for_link(search_text):
    key_item = HotelSearchKeys.query.filter_by(
        search_text=search_text).first()
    if key_item:
        logger.info("Passing hotel link")
        return {"hotel_link": key_item.base_url, "search_text": key_item.search_text}
    else:
        logger.info("Passing search text")
        return {"hotel_link": None, "search_text": search_text}

@shared_task(name='get the hotel link',bind=True,ignore_result=False)
def get_hotel_link(self,params):
    hotel_link = params["hotel_link"]
    search_text = params["search_text"]
    if hotel_link is not None:
        return {"link": hotel_link, "search_text": search_text, "task_id": self.request.id}
    else:
        decoded_search_text = urllib.parse.unquote_plus(search_text)
        with sync_playwright() as pw:
            try:
                try:
                    if browser_url:
                        browser = pw.chromium.connect_over_cdp(browser_url)
                    else:
                        browser = pw.chromium.launch(slow_mo=100)
                    context = browser.new_context(user_agent=user_agent)
                    page = context.new_page()
                    logger.info("Connecting to website")
                    page.goto(f"{search_url}{search_text}")
                    page.wait_for_load_state()

                    final_link = getHotelListPage(page, context, search_text)
                    if final_link in ["",None]:
                        raise ValueError(
                                f"Hotel link is unavailable. Please try again when searching \"{decoded_search_text}\"")
                    else:
                        #raise Exception("Error testing")
                        return {"link": final_link, "search_text": search_text, "task_id": self.request.id}
                except (Error, TimeoutError, Exception) as ex:
                    logger.error(ex)
                    raise self.retry(max_retries=1, countdown=5)
                finally:
                    if page:
                        page.close()
                    if browser:
                        browser.close()
            except (MaxRetriesExceededError) as mr:
                logger.error("Retries exceeded")
                self.update_state(
                    state=states.FAILURE,
                    meta={
                        'exc_type': type(mr).__name__,
                        'exc_message': traceback.format_exc().split('\n'),
                        'custom': '...'
                    })
                raise Ignore()
            finally:
                if page:
                    page.close()
                if browser:
                    browser.close()

@shared_task(name='save hotel link', bind=True)
def save_hotel_link(self, hotel_data):
    hotel_link = hotel_data["link"]
    task = AsyncResult(hotel_data["task_id"])
    search_text = hotel_data["search_text"]

    if task.state == "SUCCESS":
        exists = db.session.query(HotelSearchKeys.id).filter_by(
                base_url=hotel_link).first() is not None
        if not exists:
            search_item = HotelSearchKeys(
                search_text,hotel_link)
            db.session.add(search_item)
            db.session.commit()
            logger.info("Saved link to database")
        else:
            logger.info("Link already exists")
    
        return f"{site_url}{hotel_link}"
    else:
        self.update_state(state=states.IGNORED, meta={"custom": "Hotel link fetch was failed"})
        logger.error("Hotel link search was failed")
        raise Ignore()
    
@shared_task(name='generate paginated hotels', bind=True, ignore_result=False)
def generate_paginated_hotels(self,hotel_link):    
    extracted_url = hotel_link.split("//")[2]
    hotel_urls = [hotel_link]
    validated_links = []
    dash_match = [pos.start() for pos in re.finditer(r"-", extracted_url)]
    insert_pos = dash_match[1]
    counter = 0

    tasks = []
    for i in range(depth_level):
        counter += 30
        modified_url = extracted_url[:insert_pos] + \
            f"-oa{counter}" + extracted_url[insert_pos:]
        tasks.append(validate_link.s(f"{site_url}/{modified_url}"))
    
    logger.info("Executing group validate")
    job = group(tasks).apply_async()
    validated_links = job.get(disable_sync_subtasks=False)

    for link in validated_links:
        if link is not None:
            hotel_urls.append(link)

    return hotel_urls    


@shared_task(name='validate link', ignore_result=False)
def validate_link(link):
    try:
        resp = httpx.get(link, headers={"User-Agent": user_agent}, proxies=proxies, verify=False)
        if resp.status_code == 200:
            return link
        else:
            return None
    except httpx.TimeoutException:
        return None