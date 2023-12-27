import asyncio
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError
import requests
from page_scraper import scrape_list
import json
from selectolax.parser import HTMLParser
import httpx
import os
import urllib.parse
from hotel_link_generator import generate_paginated_hotels
import sys

settings_file = f"{os.path.abspath(__file__.replace('main.py', ''))}\settings.json"
browser_url = None

with open(settings_file) as json_file:
    settings = json.load(json_file)
    api_url = settings['host']
    user_agent = settings['user_agent']
    proxies = None if settings['proxies'] == "" else settings['proxies']
    username = None if settings['username'] == "" else settings['username']
    password = None if settings['password'] == "" else settings['password']
    wss_host = None if settings['wss_host'] == "" else settings['wss_host']
    depth_level = settings['depth_level']
    if username and password and wss_host:
        browser_url = f"wss://{settings['username']}:{settings['password']}@{settings['wss_host']}"


site_url = "https://www.tripadvisor.com/"
search_url = "https://www.tripadvisor.com/Search?q="


def post_results(data, update_type, message=None):
    headers = {"Content-Type": "application/json"}
    data = {"data": data, "update_type": update_type}
    status = 0
    resp_message = message

    if update_type != "post_log":
        response = requests.post(
            f"{api_url}/post-results", headers=headers, json=data, verify=False)
        status = response.status_code
        resp_message = response.json()['message']

    # add a log
    log = {"message": resp_message, "status": "SUCCESS" if status ==
           200 else "ERROR", "update_type": "post_log"}
    requests.post(f"{api_url}/post-results",
                  headers=headers, json=log, verify=False)


def postlog(message):
    post_results(None, "post_log", message)


def end_scraping(search_text):
    headers = {"Content-Type": "application/json"}
    data = {"search_text": search_text}

    requests.post(f"{api_url}/end-scraping",
                  headers=headers, json=data, verify=False)


def get_hotel_url(search_text):
    if search_text in ["", None]:
        return None

    print("Checking if location url exists")
    params = {'key': search_text}
    response = requests.get(
        f"{api_url}/search", params=params, timeout=5000)
    if response.status_code == 200:
        return response.json()['url']
    else:
        return None


async def getHotelListPage(page, context, search_text):
    print(f"Searching for {search_text} on {page.url}")
    top_result = page.locator(
        "div[data-widget-type='TOP_RESULT'] div.result-title").first
    async with context.expect_page() as new_page_info:
        await top_result.click()
    new_page = await new_page_info.value

    await new_page.wait_for_load_state()
    hotel_link = new_page.locator(
        "div[data-test-target='nav-links'] a").filter(has_text="Hotels")
    return await hotel_link.get_attribute("href")


async def getHotelData(hotel):
    url = hotel.css_first("a").attributes["href"]
    return f"{site_url}{url}"


async def getHotelUrls(client, full_link):
    try:
        r = await client.get(full_link)
        if r.status_code == 200:
            page = HTMLParser(r.text)
            titles = page.css("div[data-automation='hotel-card-title']")

            tasks = []
            for title in titles:
                tasks.append(asyncio.create_task(getHotelData(title)))
            hotel_urls = await asyncio.gather(*tasks, return_exceptions=True)
            return hotel_urls
        else:
            return None
    except httpx.TimeoutException:
        return None


async def start_scraping(search_text, hotel_link):
    decoded_search_text = urllib.parse.unquote_plus(search_text)

    print("Start deep-search")
    paginated_urls = await generate_paginated_hotels(hotel_link, site_url, user_agent, proxies, depth_level)
    print("Collected URLs:", len(paginated_urls))

    print("Getting hotel urls")
    tasks = []
    async with httpx.AsyncClient(headers={"User-Agent": user_agent}, proxies=proxies, verify=False) as client:
        for url in paginated_urls:
            tasks.append(asyncio.create_task(getHotelUrls(client, url)))
        extracted_hotel_urls = await asyncio.gather(*tasks, return_exceptions=True)

    hotel_urls = []
    for hotel_url in extracted_hotel_urls:
        if hotel_url is not None and not isinstance(hotel_url, Exception):
            hotel_urls.append(hotel_url)

    print("Raw list:", len(hotel_urls))
    if len(hotel_urls) == 0:
        raise ValueError(
            f"No hotels found. Please try again when searching \"{decoded_search_text}\"")

    final_hotel_urls = [x for xs in hotel_urls for x in xs]
    print("Flattened:", len(final_hotel_urls))
    print("Getting hotel names")
    hotel_list = await scrape_list(final_hotel_urls, user_agent, proxies)
    if len(hotel_list) == 0:
        raise ValueError(
            f"Unable to fetch hotels. Please try again when searching \"{decoded_search_text}\"")

    # submit data to server
    post_results(
        {"results": hotel_list, "search_text": decoded_search_text}, "send_hotel_list")


async def main(search_text):
    decoded_search_text = urllib.parse.unquote_plus(search_text)
    full_link = get_hotel_url(decoded_search_text)
    exit_code = 0
    print(full_link)

    try:
        if full_link is None:
            browser = None
            async with async_playwright() as pw:
                print("Connecting to browser")
                if browser_url:
                    browser = await pw.chromium.connect_over_cdp(browser_url)
                else:
                    browser = await pw.chromium.launch(slow_mo=100)
                context = await browser.new_context(user_agent=user_agent)
                page = await context.new_page()
                print("Connecting to website")
                await page.goto(f"{search_url}{search_text}", timeout=120000)
                await page.wait_for_load_state()

                hotel_link = await getHotelListPage(page, context, decoded_search_text)
                if hotel_link in ["", None]:
                    raise ValueError(
                        f"Hotel link is unavailable. Please try again when searching \"{decoded_search_text}\"")

                full_link = f"{site_url}{hotel_link}"
                post_results({"search_text": decoded_search_text, "base_url": full_link},
                             "send_hotel_link")

                await browser.close()

        await start_scraping(search_text, full_link)

    except requests.exceptions.Timeout:
        message = f"Timeout error occured when searching \"{decoded_search_text}\""
        print(message)
        postlog(message)
        exit_code = 1
    except httpx.RequestError:
        print(message)
        message = f"There was an error occured during hotel search requests for \"{decoded_search_text}\""
        postlog(message)
        exit_code = 1
    except PWTimeoutError:
        await browser.close()
        message = f"Timeout error occured when searching \"{decoded_search_text}\""
        print(message)
        postlog(message)
        exit_code = 1
    except ValueError as err:
        message = f"An error occured when searching \"{decoded_search_text}\": {err.args[0]}"
        print(message)
        postlog(message)
        exit_code = 1
    except Exception as e:
        message = f"An unknown error has occured when searching \"{decoded_search_text}\""
        print(message)
        print(e)
        postlog(message)
        exit_code = 1
    finally:
        end_scraping(search_text)
        sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main("florida"))
