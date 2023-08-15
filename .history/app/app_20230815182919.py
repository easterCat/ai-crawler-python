import asyncio
import json
import os

import aiofiles
import aiohttp
import requests
from flask import Flask, render_template, request, Response

app = Flask(__name__)

result_urls = None

total = 0


@app.route('/')
async def render_html():
    data = await read_json_files()
    # 渲染模板并返回HTML响应
    return render_template('template.html', data={'list': data, 'total': len(data), 'allow': total})


@app.route('/draw', methods=['GET', 'POST'])
def draw():
    if request.method == 'GET':
        return render_template('draw.html', data={'images': [], 'prompt': ''})
    else:
        prompt = request.form['prompt']
        negative_prompt = request.form['negative_prompt']
        n_iter = request.form['n_iter']
        width = request.form['width']
        height = request.form['height']
        steps = request.form['steps']
        url = request.args.get('url')

        headers = {"Content-Type": "application/json"}
        request_json = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "n_iter": int(n_iter) if n_iter else 12,
            "width": int(width) if width else 600,
            "height": int(height) if height else 800,
            "steps": int(steps) if steps else 30,
        }

        print(f"URL: {url}")
        print(f"Prompt: {prompt}")
        print(f"Negative Prompt: {negative_prompt}")
        print("开始绘制,等待中......")

        is_ajax_request = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        try:
            response = requests.post(url + '/sdapi/v1/txt2img', json=request_json, headers=headers)
            json_data = response.json()
            images = json_data.get("images", [])

            if is_ajax_request:
                return Response(images, mimetype='application/json')
            else:
                return render_template('draw.html', data={'images': images, 'prompt': prompt})
        except Exception:
            pass
        if is_ajax_request:
            return Response([], mimetype='application/json')
        else:
            return render_template('draw.html', data={'images': [], 'prompt': ''})


@app.route("/test", methods=['GET', 'POST'])
async def test_html():
    global result_urls

    # if request.method == 'GET':
    #     return render_template('template.html', data={'list': [], 'total': 0, 'allow': 0})

    if result_urls is None:
        print("当前没有验证,重新获取喽!!!!")
        data = await read_json_files()
        timeout = aiohttp.ClientTimeout(sock_read=60)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            print('-----------当前可用域名------------')
            tasks = []
            for item in data:
                task = asyncio.create_task(scan_port(session, item))
                tasks.append(task)
            result_urls = await asyncio.gather(*tasks)
            print(f'-----------结束 {total}/{len(data)}------------')

    is_ajax_request = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    print(request.headers)
    if is_ajax_request:
        result = json.dumps(result_urls)
        return Response(result, mimetype='application/json')
    # 渲染模板并返回HTML响应
    else:
        return render_template('template.html', data={'list': result_urls, 'total': len(result_urls), 'allow': total})


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
            "prompt": "(loli,little loli),pettie,black bodysuit,see-through,covered nipples,",
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
