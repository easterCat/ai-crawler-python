import asyncio
import json
import pathlib
from datetime import datetime

import aiohttp
from tqdm import tqdm

# BASE_URL = 'http://region-3.seetacloud.com'
# BASE_URL = 'http://region-31.seetacloud.com'
# BASE_URL = 'http://region-41.seetacloud.com'
# BASE_URL = 'http://region-4.seetacloud.com'
BASE_URL = 'http://region-8.seetacloud.com'
# BASE_URL = 'http://region-101.seetacloud.com'
# BASE_URL = 'http://region-9.seetacloud.com'

online = []


async def scan_port(session, port, progress_bar):
    url = f"{BASE_URL}:{port}"
    try:
        async with session.get(url) as response:
            if 200 <= response.status < 300:
                response_text = await response.text()
                if 'Stable' in response_text:
                    online.append(url)
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

    file_path = pathlib.Path(f'./scan_result-{datetime.now().strftime("%Y_%m_%d_%H:%M")}.json')

    with file_path.open('w', encoding='u8') as fp:
        json.dump(online, fp, ensure_ascii=False)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
