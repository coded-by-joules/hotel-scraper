import httpx
import re
import asyncio


async def verify_hotel_link(client, link):
    try:
        resp = await client.get(link)
        if resp.status_code == 200:
            return link
        else:
            return None
    except httpx.TimeoutException:
        return None

# https://www.tripadvisor.com//Hotels-g28964-Texas-Hotels.html


async def generate_paginated_hotels(hotel_link, site_url, user_agent, proxies, depth_level):
    extracted_url = hotel_link.split("//")[2]
    hotel_urls = [hotel_link]
    validated_links = []
    dash_match = [pos.start() for pos in re.finditer(r"-", extracted_url)]
    insert_pos = dash_match[1]
    counter = 0

    async with httpx.AsyncClient(headers={"User-Agent": user_agent}, proxies=proxies, verify=False) as client:
        tasks = []
        for i in range(depth_level):
            counter += 30
            modified_url = extracted_url[:insert_pos] + \
                f"-oa{counter}" + extracted_url[insert_pos:]
            tasks.append(asyncio.create_task(
                verify_hotel_link(client, f"{site_url}/{modified_url}")))
        validated_links = await asyncio.gather(*tasks, return_exceptions=True)

    for link in validated_links:
        if link is not None and not isinstance(link, Exception):
            hotel_urls.append(link)

    return hotel_urls

if __name__ == "__main__":
    asyncio.run(generate_paginated_hotels(
        "https://www.tripadvisor.com//Hotels-g28964-Texas-Hotels.html"))
