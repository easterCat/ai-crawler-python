import asyncio
import json
import pathlib
import re
import time

import aiohttp
from tqdm import tqdm

online = []

servers = [
    "region-3",
    "region-4",
    "region-8",
    "region-9",
    "region-31",
    "region-41",
    "region-42",
    "region-101",
    "region-102",
]

# servers = ["region-{}".format(item) for item in range(1, 50)]
# servers = ["region-{}".format(item) for item in range(50, 100)]
# servers = ["region-{}".format(item) for item in range(100, 150)]
# servers = ["region-{}".format(item) for item in range(150, 200)]


async def scan_port(session, server, port, batch_progress_bar):
    url = f"http://{server}.seetacloud.com:{port}"
    # url = f"http://localhost:{port}"

    try:
        async with session.get(url) as response:
            if 200 <= response.status < 300:
                html = await response.text()
                if 'Stable' in html:
                    pattern = re.compile(r'(?<=")[^"]*\.safetensors[\s\[\]a-z0-9]*(?=")')
                    result = pattern.findall(html)
                    temp = []
                    for item in result:
                        if item not in temp and 'lora/' not in item and 'Lora/' not in item:
                            temp.append(item)
                    online.append({"url": url, "models": temp})
    except aiohttp.ClientError:
        pass
    except asyncio.TimeoutError:
        pass
    except Exception:
        pass
    batch_progress_bar.update(1)


async def main():
    timeout = aiohttp.ClientTimeout(sock_read=20)
    ports_to_scan = range(10000, 65536)
    batch_size = 3000
    total_batches = (len(ports_to_scan) - 1) // batch_size + 1
    total_progress_bar = tqdm(total=len(ports_to_scan) * len(servers), desc="Overall Progress", unit="port",
                              position=0, leave=True)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for server in servers:
            for batch in range(total_batches):
                start_idx = batch * batch_size
                end_idx = min((batch + 1) * batch_size, len(ports_to_scan))

                batch_ports = ports_to_scan[start_idx:end_idx]
                batch_progress_bar = tqdm(total=len(batch_ports),
                                          desc=f"Scanning {server} Ports - Batch {batch + 1}/{total_batches}",
                                          unit="port",
                                          position=0, leave=True)

                tasks = [scan_port(session, server, port, batch_progress_bar) for port in batch_ports]
                await asyncio.gather(*tasks)

                batch_progress_bar.close()
                total_progress_bar.update(len(batch_ports))

                sleep_time = 6 + batch % 3
                await asyncio.sleep(sleep_time)

                if end_idx >= 55536:
                    break

    total_progress_bar.close()

    file_path = pathlib.Path(f'./global_scan_result_{time.time()}.json')

    if len(servers) == 1:
        file_path = pathlib.Path(f'./{servers[0]}_scan_result_{time.time()}.json')

    with file_path.open('w', encoding='u8') as fp:
        json.dump(online, fp, ensure_ascii=False)


if __name__ == "__main__":
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())
    # loop.close()
    asyncio.run(main())
