import asyncio
import base64
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
    if "sd_model_checkpoint" in opt_json:
        cur_model = opt_json["sd_model_checkpoint"]
    else:
        cur_model = ""
    cur_hash = opt_json["sd_checkpoint_hash"][0:10]
    if "[" in cur_model and "]" in cur_model:
        cur_model_name = f"{cur_model}"
    else:
        cur_model_name = f"{cur_model} [{cur_hash}]"
    print(f"当前的模型：{cur_model_name}")

    if request.method == "GET":
        return render_template(
            "draw.html",
            data={
                "images": [],
                "prompt": "",
                "models": models_json,
                "cur_model_name": cur_model_name,
            },
        )
    else:
        prompt = request.form["prompt"]
        negative_prompt = request.form["negative_prompt"]
        n_iter = request.form["n_iter"]
        batch_size = request.form["batch_size"]
        width = request.form["width"]
        height = request.form["height"]
        steps = request.form["steps"]
        model = request.form["model"]

        headers = {"Content-Type": "application/json"}
        request_json = {
            "denoising_strength": 0,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "seed": -1,  # 种子，随机数
            "batch_size": int(batch_size) if batch_size else 1,  # 每次张数
            "n_iter": int(n_iter) if n_iter else 12,  # 生成批次
            "steps": int(steps) if steps else 30,  # 生成步数
            "cfg_scale": 8,  # 关键词相关性
            "width": int(width) if width else 600,  # 宽度
            "height": int(height) if height else 800,  # 高度
            "restore_faces": "false",  # 脸部修复
            "tiling": "false",  # 可平铺
            "override_settings": {
                "sd_model_checkpoint": model
            },  # 一般用于修改本次的生成图片的stable diffusion模型，用法需保持一致
            "sampler_index": "Euler a",  # 采样方法
        }

        print("----------------文生图的信息----------------")
        print(f"请求接口: {url}")
        print(f"使用模型: {model}")
        print(f"正面词条: {prompt}")
        print(f"负面词条: {negative_prompt}")
        print(f"生成数量: {n_iter}")
        print("----------------开始生成,等待中----------------")

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
                        "cur_model_name": cur_model_name,
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
                    "cur_model_name": cur_model_name,
                },
            )


@app.route("/img2img", methods=["POST"])
def img2img():
    url = request.args.get("url")
    prompt = request.form["prompt"]
    negative_prompt = request.form["negative_prompt"]
    n_iter = request.form["n_iter"]
    batch_size = request.form["batch_size"]
    width = request.form["width"]
    height = request.form["height"]
    steps = request.form["steps"]
    denoising_strength = request.form["denoising_strength"]
    model = request.form["model"]
    file = request.files["image"]

    if file:
        file_data = file.read()
        encoded_file = base64.b64encode(file_data).decode("utf-8")

        headers = {"Content-Type": "application/json"}
        request_json = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "override_settings": {
                "sd_model_checkpoint": model
            },  # 一般用于修改本次的生成图片的stable diffusion模型，用法需保持一致
            "seed": -1,  # 种子，随机数
            "batch_size": int(batch_size) if batch_size else 1,  # 每次张数
            "n_iter": int(n_iter) if n_iter else 12,  # 生成批次
            "steps": int(steps) if steps else 30,  # 生成步数
            "cfg_scale": 8,  # 关键词相关性
            "width": int(width) if width else 600,  # 宽度
            "height": int(height) if height else 800,  # 高度
            "restore_faces": "false",  # 脸部修复
            "tiling": "false",  # 可平铺
            "eta": 0,
            "script_args": [],
            "sampler_index": "Euler a",  # 采样方法
            "init_images": [encoded_file],
            # "mask": encoded_file,
            "resize_mode": 1,
            "denoising_strength": float(denoising_strength)
            if denoising_strength
            else 0.5,
            # "mask_blur": 10,
            "inpainting_fill": 1,
            "inpaint_full_res": "true",
            "inpaint_full_res_padding": 32,
            "inpainting_mask_invert": 1,
        }

        print("----------------图生图的信息----------------")
        print(f"请求接口: {url}")
        print(f"使用模型: {model}")
        print(f"正面词条: {prompt}")
        print(f"负面词条: {negative_prompt}")
        print(f"生成数量: {n_iter}")
        print("----------------开始生成,等待中----------------")

        response = requests.post(
            url + "/sdapi/v1/img2img", json=request_json, headers=headers
        )
        json_data = response.json()
        images = json_data.get("images", [])
        response = jsonify({"images": images})
        response.mimetype = "application/json"
        return response

    response = jsonify({"images": []})
    response.mimetype = "application/json"
    return response


@app.route("/update_model", methods=["POST"])
def update_model():
    model_name = request.form.get("model_name")
    url = request.form.get("url")
    option_payload = {"sd_model_checkpoint": model_name}
    headers = {"Content-Type": "application/json"}
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
    unique_list = []
    for d in data:
        if d not in unique_list:
            unique_list.append(d)
    return unique_list


async def scan_port(session, item):
    global total
    api = item["url"] + "/sdapi/v1/txt2img"
    try:
        headers = {"Content-Type": "application/json"}
        async with session.post(
                api,
                data=json.dumps(
                    {
                        "n_iter": 1,
                        "width": 512,
                        "height": 768,
                        "prompt": "best quality,masterpiece,(Preschooler:1.5),(toddler:1.5),(loli:1.5),(little loli:1.5),(Child:1.5),(large_breasts:1.3),petite,skinny,ribs,black bodysuit,(see through:1.4),covered_nipples,covered_erect_nipples,covered_breasts,covered_navel,",
                        "negative_prompt": "sketch,duplicate,ugly,text,error,logo,monochrome,worst face,(bad and mutated hands:1.3),(worst quality:1.3),(low quality:1.3),(normal quality:1.3),(blurry:1.3),(missing fingers),multiple limbs,bad anatomy,(interlocked fingers),Ugly Fingers,extra digit,extra hands,extra fingers,extra legs,extra arms,fewer digits,(deformed fingers),(long fingers),signature,watermark,username,multiple panels,",
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
