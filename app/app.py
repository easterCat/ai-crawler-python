import asyncio
import json
import os

import aiofiles
import aiohttp
import requests
from flask import Flask, jsonify, render_template, request, Response

app = Flask(__name__)

result_urls = None
total = 0


@app.route("/")
async def render_html():
    data = await read_json_files()
    return render_template(
        "template.html", data={"list": data, "total": len(data), "allow": total}
    )


@app.route("/draw", methods=["GET", "POST"])
def draw():
    url = request.args.get("url")
    model_response = requests.get(url + "/sdapi/v1/sd-models")
    models_json = model_response.json()

    opt_response = requests.get(url + "/sdapi/v1/options")
    opt_json = opt_response.json()
    cur_model = opt_json["sd_model_checkpoint"]

    if request.method == "GET":
        try:
            opt_response = requests.get(url + "/sdapi/v1/options")
            opt_json = opt_response.json()
            print(f"当前的模型：{opt_json['sd_model_checkpoint']}")
        except Exception as e:
            print(e)
            pass
        return render_template(
            "draw.html",
            data={
                "images": [],
                "prompt": "",
                "models": models_json,
                "cur_model": cur_model,
            },
        )
    else:
        prompt = request.form["prompt"]
        negative_prompt = request.form["negative_prompt"]
        n_iter = request.form["n_iter"]
        width = request.form["width"]
        height = request.form["height"]
        steps = request.form["steps"]

        headers = {"Content-Type": "application/json"}
        request_json = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "n_iter": int(n_iter) if n_iter else 12,
            "width": int(width) if width else 600,
            "height": int(height) if height else 800,
            "steps": int(steps) if steps else 30,
        }

        print("绘制图片的信息......")
        print(f"请求接口: {url}")
        print(f"正面词条: {prompt}")
        print(f"负面词条: {negative_prompt}")
        print(f"生成数量: {n_iter}")
        print("开始绘制,等待中......")

        is_ajax_request = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        try:
            response = requests.post(
                url + "/sdapi/v1/txt2img", json=request_json, headers=headers
            )
            json_data = response.json()
            images = json_data.get("images", [])

            if is_ajax_request:
                response = jsonify({"images": images})
                response.mimetype = "application/json"
                return response
            else:
                return render_template(
                    "draw.html",
                    data={
                        "images": images,
                        "prompt": prompt,
                        "models": models_json,
                        "cur_model": cur_model,
                    },
                )
        except Exception as e:
            print(e)
            pass

        if is_ajax_request:
            response = jsonify({"images": []})
            response.mimetype = "application/json"
            return response
        else:
            return render_template(
                "draw.html",
                data={
                    "images": [],
                    "prompt": "",
                    "models": models_json,
                    "cur_model": cur_model,
                },
            )


@app.route("/change_model", methods=["POST"])
def change_model():
    model_name = request.form.get("model_name")
    url = request.form.get("url")
    option_payload = {
        "sd_model_checkpoint": model_name,
    }
    headers = {"Content-Type": "application/json"}
    print(option_payload)
    response = requests.post(
        url + "/sdapi/v1/options", json=option_payload, headers=headers
    )

    if response.status_code == 200:
        return Response("success")
    else:
        return Response("failed")


@app.route("/test", methods=["GET", "POST"])
async def test_html():
    global result_urls

    # if request.method == 'GET':
    #     return render_template('template.html', data={'list': [], 'total': 0, 'allow': 0})

    if result_urls is None:
        print("当前没有验证,重新获取喽!!!!")
        data = await read_json_files()
        timeout = aiohttp.ClientTimeout(sock_read=60)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            print("-----------当前可用域名------------")
            tasks = []
            for item in data:
                task = asyncio.create_task(scan_port(session, item))
                tasks.append(task)
            result_urls = await asyncio.gather(*tasks)
            print(f"-----------结束 {total}/{len(data)}------------")
    else:
        print("有緩存，省事了")

    is_ajax_request = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if is_ajax_request:
        result = json.dumps(result_urls)
        return Response(result, mimetype="application/json")
    else:
        return render_template(
            "template.html",
            data={"list": result_urls, "total": len(result_urls), "allow": total},
        )


async def read_json_files():
    data = []
    directory = os.path.join(os.path.dirname(__file__), "../autodl")
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            file_path = os.path.join(directory, filename)
            async with aiofiles.open(file_path, "r", encoding="utf-8") as json_file:
                file_data = json.loads(await json_file.read())
                data.extend(file_data)
    return data


async def scan_port(session, item):
    global total
    api = item["url"] + "/sdapi/v1/txt2img"
    try:
        headers = {"Content-Type": "application/json"}
        async with session.post(
            api,
            data=json.dumps(
                {
                    "width": 512,
                    "height": 768,
                    "prompt": "1loli,(loli:1.3),petite,skinny,ribs,long hair,low twintails,black bodysuit,black leotard,(see through:1.2),covered nipples,covered navel,",
                    "negative_prompt": "sketch,duplicate,ugly,text,error,logo,monochrome,worstface,(bad and mutated hands:1.3),(worst quality:1.3),(low quality:1.3),(normal quality:1.3),(blurry:1.3),(missing fingers),multiple limbs,badanatomy,(interlocked fingers),Ugly Fingers,extra digit,extra hands,extrafingers,extra legs,extra arms,fewer digits,(deformed fingers),(longfingers),signature,watermark,username,multiple panels,",
                }
            ),
            headers=headers,
        ) as response:
            if 200 <= response.status < 300:
                html_json = await response.json()
                images = html_json.get("images", [])
                if images[0] is not None:
                    total += 1
                    print(item["url"])
                item["images"] = images
                return item
            else:
                return item
    except Exception:
        pass
    return item


if __name__ == "__main__":
    app.run(port=9999)
