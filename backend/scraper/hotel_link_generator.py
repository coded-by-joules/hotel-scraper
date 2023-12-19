import httpx
import re
from main import site_url, user_agent, proxies, depth_level
import asyncio

async def verify_hotel_link(client, link):
    pass

# https://www.tripadvisor.com//Hotels-g28964-Texas-Hotels.html
async def generate_paginated_hotels(hotel_link):
    extracted_url = hotel_link.split("//")[2]
    hotel_urls = [hotel_link]
    dash_match = [pos.start() for pos in re.finditer(r"-", extracted_url)]
    insert_pos = dash_match[1]
    counter = 0

    async with httpx.AsyncClient(headers={"User-Agent": user_agent}, proxies=proxies, verify=False) as client:
        tasks = []
        for i in range(depth_level):
            counter += 30
            modified_url = extracted_url[:insert_pos] + f"-oa{counter}" + extracted_url[insert_pos:]
            tasks.append(asyncio.create_task(verify_hotel_link(client, modified_url)))

    return hotel_urls

if __name__ == "__main__":
    asyncio.run(generate_paginated_hotels("https://www.tripadvisor.com//Hotels-g28964-Texas-Hotels.html"))