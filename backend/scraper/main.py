import asyncio
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError
import requests
from page_scraper import scrape_list
import json
from selectolax.parser import HTMLParser
import httpx

with open("settings.json") as json_file:
    settings = json.load(json_file)
    api_url = settings['host']
    user_agent = settings['user_agent']
    proxies = None if settings['proxies'] == "" else settings['proxies']
   
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

    log = {"message": resp_message, "status": "SUCCESS" if status ==
           200 else "ERROR", "update_type": "post_log"}
    requests.post(f"{api_url}/post-results",
                  headers=headers, json=log, verify=False)


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
        "div[data-widget-type='TOP_RESULT'] div.result-title")
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


async def getHotelUrls(full_link):
    r = requests.get(full_link, headers={"User-Agent": user_agent})
    page = HTMLParser(r.text)
    titles = page.css("div[data-automation='hotel-card-title']")

    tasks = []
    for title in titles:
        tasks.append(asyncio.create_task(getHotelData(title)))
    hotel_urls = await asyncio.gather(*tasks, return_exceptions=True)
    return hotel_urls


async def main(search_text):
    full_link = get_hotel_url(search_text)
    print(full_link)
    try:
        if full_link is None:
            browser = None
            async with async_playwright() as pw:
                print("Connecting to browser")
                browser = await pw.chromium.launch(slow_mo=2000)
                context = await browser.new_context(user_agent=user_agent)
                page = await context.new_page()
                print("Connecting to website")
                await page.goto(f"{search_url}{search_text}", timeout=120000)
                await page.wait_for_load_state()

                hotel_link = await getHotelListPage(page, context, search_text)
                if hotel_link in ["", None]:
                    raise ValueError(
                        f"Hotel link is unavailable. Please try again when searching \"{search_text}\"")

                full_link = f"{site_url}{hotel_link}"
                post_results({"search_text": search_text, "base_url": full_link},
                             "send_hotel_link", f"\"{search_text}\" search link added to database")

                await browser.close()

        print("Getting hotel urls")
        hotel_urls = await getHotelUrls(full_link)
        if len(hotel_urls) == 0:
            raise ValueError(
                f"No hotels found. Please try again when searching \"{search_text}\"")

        print("Getting hotel names")
        hotel_list = await scrape_list(hotel_urls, user_agent, proxies)
        if len(hotel_list) == 0:
            raise ValueError(
                f"Unable to fetch hotels. Please try again when searching \"{search_text}\"")

        # submit data to server
        post_results({"results": hotel_list, "search_text": search_text}, "send_hotel_list")
    except requests.exceptions.Timeout:
        message = f"Timeout error occured when searching \"{search_text}\""
        print(message)
        post_results(None, "postlog", message)
    except httpx.RequestError:
        print(message)
        message = f"There was an error occured during hotel search requests for \"{search_text}\""
        post_results(None, "postlog", message)
    except PWTimeoutError:
        await browser.close()
        message = f"Timeout error occured when searching \"{search_text}\""
        print(message)
        post_results(None, "postlog", message)
    except ValueError as err:
        message = f"An error occured when searching \"{search_text}\": {err.args[0]}"
        print(message)
        post_results(None, "postlog", message)
    except Exception as e:
        message = f"An unknown error has occured when searching \"{search_text}\""
        print(message)
        print(e)


if __name__ == "__main__":
    asyncio.run(main("alabama"))
