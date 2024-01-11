from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
from celery import shared_task
import json
import urllib
import logging

site_url = "https://www.tripadvisor.com/"
search_url = "https://www.tripadvisor.com/Search?q="

settings_file = "settings.json"
browser_url = None

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

@shared_task(bind=True,ignore_result=False, max_retries=1)
def get_hotel_link(self,search_text):
    try:
        decoded_search_text = urllib.parse.unquote_plus(search_text)
        with sync_playwright() as pw:
            print("Connecting to browser")
            if browser_url:
                browser = pw.chromium.connect_over_cdp(browser_url)
            else:
                browser = pw.chromium.launch(slow_mo=100)
            context = browser.new_context(user_agent=user_agent)
            page = context.new_page()
            print("Connecting to website")
            page.goto(f"{search_url}{search_text}", timeout=120000)
            page.wait_for_load_state()

            final_link = getHotelListPage(page, context, search_text)
            if final_link in ["",None]:
                raise ValueError(
                        f"Hotel link is unavailable. Please try again when searching \"{decoded_search_text}\"")
            else:
                return final_link
    except (ValueError, PWTimeoutError, Exception) as err:
        print(err)
        raise self.retry(exc=err)
    