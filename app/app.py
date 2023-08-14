import asyncio
import json
import os

import aiofiles
import aiohttp
from flask import Flask, render_template

app = Flask(__name__)

total = 0


@app.route('/')
async def render_html():
    data = await read_json_files()
    # 渲染模板并返回HTML响应
    return render_template('template.html', data={'list': data, 'total': len(data), 'allow': total})


@app.route("/test")
async def test_html():
    data = await read_json_files()
    timeout = aiohttp.ClientTimeout(sock_read=60)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        print('-----------当前可用域名------------')
        tasks = []
        for item in data:
            task = asyncio.create_task(scan_port(session, item))
            tasks.append(task)
        result = await asyncio.gather(*tasks)
        print(f'-----------结束 {total}/{len(data)}------------')

    # 渲染模板并返回HTML响应
    return render_template('template.html', data={'list': result, 'total': len(result), 'allow': total})


async def read_json_files():
    data = []
    directory = os.path.join(os.path.dirname(__file__), '../autodl')
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as json_file:
                file_data = json.loads(await json_file.read())
                data.extend(file_data)
    return data


async def scan_port(session, item):
    global total
    api = item['url'] + '/sdapi/v1/txt2img'
    try:
        headers = {'Content-Type': 'application/json'}
        async with session.post(api, data=json.dumps({
            "prompt": "1girl,loli,black bodysuit,see-through,covered navel,spread legs,",
            "negative_prompt": "(worst quality:1.3),(low quality:1.3),(normal quality:1.3),",
            # "height": 768
        }), headers=headers) as response:
            if 200 <= response.status < 300:
                html_json = await response.json()
                images = html_json.get("images", [])
                if images[0] is not None:
                    total += 1
                    print(item['url'])
                item['images'] = images
                return item
            else:
                return item
    except Exception:
        pass
    return item


if __name__ == '__main__':
    app.run(port=9999)
