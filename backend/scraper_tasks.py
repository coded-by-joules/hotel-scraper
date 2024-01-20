from playwright.sync_api import sync_playwright, Error, TimeoutError
from celery import shared_task, states, group
from celery.result import AsyncResult
import json
import urllib
import logging
from .database import db, HotelSearchKeys, HotelInfo
from celery.exceptions import MaxRetriesExceededError
import traceback
import re
import httpx
from selectolax.parser import HTMLParser

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

class ScrapingError(Exception):
    pass

#
# UTILITY FUNCTIONS
#
def nodes(node):
    while node.parent:
        yield node
        node = node.parent
    yield node            

def start_scraping_async(search_text, code):
    chain = (check_db_for_link.s(search_text) | 
             get_hotel_link.s().set(retry=True) |
             save_hotel_link.s() |
             generate_paginated_hotels.s() |
             start_scraping.s() |
             start_scraping_hotels.s() |
             save_hotels_to_db.s(queue_id=code)).apply_async(link_error=error_on_scraping.s(queue_id=code))
    
    task_collection = [node.id for node in reversed(list(nodes(chain)))]
    return task_collection

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
def check_db_for_link(search_text,ignore_result=False):
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
                        # raise Exception("Error testing")
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
                raise ScrapingError("Error during looking for hotel url") from None
            finally:
                if page:
                    page.close()
                if browser:
                    browser.close()

@shared_task(name='save hotel link', bind=True,ignore_result=False)
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
    
        return {"search_text": search_text, "url": f"{site_url}{hotel_link}"}
    else:
        self.update_state(state=states.FAILURE, meta={"custom": "Hotel link fetch was failed"})
        logger.error("Hotel link search was failed")
        raise ScrapingError("Error during fetching hotel link") from None
    
@shared_task(name='generate paginated hotels', bind=True, ignore_result=False)
def generate_paginated_hotels(self,data):
    hotel_link = data["url"]
    search_text = data["search_text"]

    extracted_url = hotel_link.split("//")[2]
    hotel_urls = [hotel_link]
    validated_links = []
    dash_match = [pos.start() for pos in re.finditer(r"-", extracted_url)]
    insert_pos = dash_match[1]
    counter = 0

    tasks = []
    for _ in range(depth_level):
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

    return {"search_text": search_text, "urls": hotel_urls}


@shared_task(name='validate link', ignore_result=False)
def validate_link(link):
    try:
        resp = httpx.get(link, headers={"User-Agent": user_agent}, proxies=proxies, verify=False)
        if resp.status_code == 200:
            return link
        else:
            return None
    except (httpx.TimeoutException, httpx.ConnectError, Exception):
        return None
    
@shared_task(name='start scraping', bind=True, ignore_result=False)
def start_scraping(self, data):
    search_text = data["search_text"]
    hotel_links = data["urls"]

    if len(hotel_links) > 0:
        tasks = []
        for url in hotel_links:
            tasks.append(get_hotel_urls.s(url))
        
        logger.info("Getting hotel URLs")
        job = group(tasks).apply_async()
        extracted_hotel_urls = job.get(disable_sync_subtasks=False)

        hotel_urls = []
        for hotel_url in extracted_hotel_urls:
            if hotel_url is not None:
                hotel_urls.append(hotel_url) 

        logger.info("Flattening the List")
        final_hotel_urls = [x for xs in hotel_urls for x in xs]

        return {"search_text": search_text, "urls": final_hotel_urls}
    else:
        self.update_state(state=states.FAILURE, meta={"custom": "No link to scrape"})
        logger.error("No link to scrape")
        raise ScrapingError("Error during searching for links to scraping, or there's no link to scrape") from None
    
@shared_task(name='get hotel urls', ignore_result=False)
def get_hotel_urls(hotel_page_link):
    try:
        resp = httpx.get(hotel_page_link, headers={"User-Agent": user_agent}, proxies=proxies, verify=False)
        if resp.status_code == 200:
            page = HTMLParser(resp.text)
            titles = page.css("div[data-automation='hotel-card-title']")

            hotel_urls = []
            for title in titles:
                url = title.css_first("a").attributes["href"]
                hotel_urls.append(f"{site_url}{url}")
            
            return hotel_urls
        else:
            return None
    except (httpx.TimeoutException, httpx.ConnectError, Exception):
        return None
    
@shared_task(name="start scraping hotel", bind=True, ignore_result=False)
def start_scraping_hotels(self, data):
    search_text = data["search_text"]
    hotel_list = data["urls"]
    if len(hotel_list) > 0:
        tasks = []
        for url in hotel_list:
            tasks.append(scrape_page.s(url))
        
        logger.info("Scraping details in the URLs")
        job = group(tasks).apply_async()
        results = job.get(disable_sync_subtasks=False)

        hotel_data = []
        for result in results:
            if result is not None:
                hotel_data.append(result) 
        
        return {"search_text": search_text, "data": hotel_data}
    else:
        self.update_state(state=states.FAILURE, meta={"custom": "No link to scrape"})
        logger.error("No link to scrape")
        raise ScrapingError("Error during scraping for data, or no data to scrape")
    
@shared_task(name="scrape hotel page", ignore_result=False)
def scrape_page(url):
    try:
        resp = httpx.get(url, headers={"User-Agent": user_agent}, proxies=proxies, verify=False)
        if resp.status_code == 200:
            page = HTMLParser(resp.text)
            hotel_element = page.css_first("h1#HEADING")
            address_element = None
            if hotel_element:
                address_element = hotel_element.parent.parent.next.child.child.next
            phone_element = page.css_first("div[data-blcontact='PHONE ']")

            if hotel_element is None:
                return None
            return {"name": hotel_element.text() if hotel_element else None,
                    "phone": phone_element.text() if phone_element else None,
                    "address": address_element.text() if address_element else None,
                    "url": url}
        else:
            return None
    except (httpx.TimeoutException, httpx.ConnectError, Exception):
        return None
    
@shared_task(name="save to database", bind=True,ignore_result=False)
def save_hotels_to_db(self, data, queue_id):
    search_text = data["search_text"]
    hotel_data = data["data"]

    if len(hotel_data) > 0:
        logger.info("Saving hotel data to database")
        searchKeyItem = HotelSearchKeys.query.filter_by(
            search_text=search_text).first()
        for result in hotel_data:
            if result:
                hotel = HotelInfo.query.filter_by(
                    hotel_name=result['name'], search_key=searchKeyItem.id).first()
                if hotel is None:
                    hotel = HotelInfo(search_id=searchKeyItem.id,
                                        hotel_name=result['name'],
                                        address=result['address'],
                                        phone=result['phone'],
                                        url=result['url'])
                    db.session.add(hotel)
                    searchKeyItem.children.append(hotel)
                else:
                    hotel.address = result['address']
                    hotel.phone = result['phone']
        db.session.commit()
        
        # emit("report_result", f"{queue_id} - Saving to data, complete")
        httpx.post("http://localhost:5000/api/report", json={"queue_id": queue_id, "message": "Saving to data, complete"})
        return f"{queue_id} - Saving to data, complete"
    else:
        self.update_state(state=states.FAILURE, meta={"custom": "No hotel data found"})
        raise ScrapingError("Error during saving data to database") from None
    
@shared_task(name="chain error handler", ignore_result=False)
def error_on_scraping(request, exc, traceback, queue_id):
    print('{0}--\n\n{1} {2}'.format(
                queue_id, request.id, exc, traceback))
    httpx.post("http://localhost:5000/api/report", json={"queue_id": queue_id, "message": f"{request.id} - {exc}"})
    return f"{request.id} - {exc}"