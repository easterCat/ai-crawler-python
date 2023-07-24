import asyncio
import json
import pathlib
import re
from datetime import datetime

import aiohttp
from tqdm import tqdm

# BASE_URL = 'region-3'
# BASE_URL = 'region-4'
# BASE_URL = 'region-8'
# BASE_URL = 'region-9'
# BASE_URL = 'region-31'
# BASE_URL = 'region-41'
# BASE_URL = 'region-42'
# BASE_URL = 'region-101'
BASE_URL = 'region-102'

online = []


async def scan_port(session, port, progress_bar):
    url = f"http://{BASE_URL}.seetacloud.com:{port}"
    try:
        async with session.get(url) as response:
            if 200 <= response.status < 300:
                html = await response.text()
                pattern = re.compile(r'(?<=")[^"]*\.safetensors[\s\[\]a-z0-9]*(?=")')
                result = pattern.findall(html)
                temp = []
                for item in result:
                    if item not in temp and 'lora/' not in item and 'Lora/' not in item:
                        temp.append(item)
                if 'Stable' in html:
                    online.append({"url": url, "models": temp})
    except aiohttp.ClientError:
        pass
    except asyncio.TimeoutError:
        pass
    progress_bar.update(1)


async def main():
    ports_to_scan = range(10000, 65536)
    total_tasks = len(ports_to_scan)
    progress_bar = tqdm(total=total_tasks, desc="Scanning Ports", unit="port")
    timeout = aiohttp.ClientTimeout(total=40 * 60)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = [scan_port(session, port, progress_bar) for port in ports_to_scan]
        await asyncio.gather(*tasks)

    progress_bar.close()

    file_path = pathlib.Path(f'./{BASE_URL} scan_result-{datetime.now().strftime("%Y_%m_%d_%H:%M")}.json')

    with file_path.open('w', encoding='u8') as fp:
        json.dump(online, fp, ensure_ascii=False)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
