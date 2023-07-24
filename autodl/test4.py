import asyncio
import json
import mimetypes
import os

import aiohttp

jsons = os.listdir('.')
requests_urls = []


async def scan_port(session, url):
    try:
        async with session.get(url) as response:
            if 200 <= response.status < 300:
                print(url)
    except Exception:
        pass


async def main():
    for json_file in jsons:
        file_type = mimetypes.guess_type(json_file)
        if file_type[0] == 'application/json':
            with open(f"./{json_file}", 'r') as f:
                f_data = json.load(f)
                for item in f_data:
                    requests_url = item
                    if 'url' in item:
                        requests_url = item['url']

                    requests_urls.append(requests_url)

    timeout = aiohttp.ClientTimeout(total=20 * 60)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        print('-----------当前可用域名------------')
        tasks = [scan_port(session, r_url) for r_url in requests_urls]
        await asyncio.gather(*tasks)
        print('-----------结束------------')


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
