import asyncio
import json
import mimetypes
import os

import aiohttp

total = 0
jsons = os.listdir('.')
requests_urls = []


# async def scan_port(session, url):
#     global total
#     try:
#         async with session.get(url) as response:
#             if 200 <= response.status < 300:
#                 html = await response.text()
#                 if "cuteyuki" in html:
#                     print(f'{url} 包含cuteyuki')
#                 if "chill" in html:
#                     print(f'{url} 包含chillout')
#                 else:
#                     print(url)
#                 total += 1
#     except Exception:
#         pass


async def scan_port(session, url):
    global total
    api = url + '/sdapi/v1/txt2img'
    try:
        headers = {'Content-Type': 'application/json'}
        async with session.post(api, data=json.dumps({
            "prompt": "loli"
        }), headers=headers) as response:
            if 200 <= response.status < 300:
                html_json = await response.json()
                images = html_json.get("images", [])
                if images[0] is not None:
                    print(url)
                    total += 1
    except Exception:
        pass


async def main():
    global total
    for json_file in jsons:
        file_type = mimetypes.guess_type(json_file)
        if file_type[0] == 'application/json':
            with open(f"./{json_file}", 'r') as f:
                f_data = json.load(f)
                for item in f_data:
                    requests_url = ''
                    if 'url' in item:
                        requests_url = item['url']
                    requests_urls.append(requests_url)

    timeout = aiohttp.ClientTimeout(sock_read=20)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        print('-----------当前可用域名------------')
        tasks = [scan_port(session, r_url) for r_url in requests_urls]
        await asyncio.gather(*tasks)
        print(f'-----------结束 {total}/{len(requests_urls)}------------')


if __name__ == "__main__":
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())
    # loop.close()
    asyncio.run(main())
