import asyncio
import re

import aiohttp

headers = {
    "Connection": "close",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 "
        "Safari/537.36"
    ),
}


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://region-3.seetacloud.com:38575/', headers=headers) as response:
            print("Status:", response.status)
            if 200 <= response.status < 300:
                print("Content-type:", response.headers['content-type'])
                html = await response.text()
                pattern = re.compile(r'(?<=")[^"]*\.safetensors[\s\[\]a-z0-9]*(?=")')
                result = pattern.findall(html)
                temp = []
                for item in result:
                    if item not in temp:
                        temp.append(item)
                print(temp)


asyncio.run(main())
