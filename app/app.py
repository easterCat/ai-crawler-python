import asyncio
import base64
import json
import os

import aiofiles
import aiohttp
from flask import Flask, jsonify, render_template, request, Response

from utils.http import MyHttp
from utils.logger import MyLogger

app = Flask(__name__)
logger = MyLogger("app/logs")
http = MyHttp()

result_urls = None
total = 0

p1 = "(masterpiece),(best quality),"
p2 = "highres,absurdres,extremely detailed,ultra-detailed,finely detail,fine detail,detailed light,detailed face,dainty,perfect face,pretty face, lush detail,highly detailed face and eyes,"
p3 = "(loli:1.5),(toddler:1.5),(child:1.5),"
p4 = "(1girl:1.3),(solo:1.3),"
p5 = "small girl,little girl,little loli,"
p6 = "(child face:1.3),(baby face:1.3),"
p7 = "very long hair,low twintails,"
p8 = "(natural breasts:1.3),(soft breasts:1.3),(huge_breasts:1.3),(sagging_breasts:1.3),(breasts_apart:1.3),"
p9 = "bodysuit,leotard,bodystocking,skin_tight,(see-through:1.3),"
p10 = "black_bodysuit,black_leotard,"
p11 = "(covered_nipples),(covered_erect_nipples),"
p12 = "covered_navel,"
p13 = "cleft_of_venus,cameltoe,clitoris,covered_clitoris,pubic hair,very pussy hair,"
p14 = "nsfw,"
p15 = "mavis dracula, smile, looking at viewer, arms behind back, black dress, striped thighhighs"
global_prompt = f"{p4}{p6}{p9}{p11}{p12}{p15}"
negative_prompt = "sketch,duplicate,ugly,text,error,logo,monochrome,worst face,(bad and mutated hands:1.5),(worst quality:1.8),(low quality:1.8),(normal quality:1.8),(blurry:1.3),(missing fingers),multiple limbs,bad anatomy,(interlocked fingers),Ugly Fingers,extra digit,extra hands,extra fingers,extra legs,extra arms,fewer digits,(deformed fingers),(long fingers),signature,watermark,username,multiple panels,"


@app.route("/")
async def render_html():
    global global_prompt
    global negative_prompt
    data = await read_json_files()
    return render_template(
        "template.html",
        data={
            "list": data,
            "total": len(data),
            "allow": total,
            "global_prompt": global_prompt,
            "negative_prompt": negative_prompt,
        },
    )


@app.route("/draw", methods=["GET", "POST"])
def draw():
    global global_prompt
    global negative_prompt
    url = request.args.get("url")
    model_response = http.get(url + "/sdapi/v1/sd-models")
    if model_response:
        models_json = model_response.json()
    else:
        models_json = []

    opt_response = http.get(url + "/sdapi/v1/options")

    if opt_response is None and request.method == "GET":
        return render_template(
            "draw.html",
            data={
                "images": [],
                "prompt": "",
                "models": models_json,
                "cur_model_name": "",
                "global_prompt": global_prompt,
                "negative_prompt": negative_prompt,
            },
        )

    opt_json = opt_response.json()
    cur_hash = opt_json["sd_checkpoint_hash"][0:10]

    if "sd_model_checkpoint" in opt_json:
        cur_model = opt_json["sd_model_checkpoint"]
    else:
        cur_model = ""

    if "[" in cur_model and "]" in cur_model:
        cur_model_name = f"{cur_model}"
    else:
        cur_model_name = f"{cur_model} [{cur_hash}]"

    logger.info(f"当前的模型：{cur_model_name}")

    if request.method == "GET":
        return render_template(
            "draw.html",
            data={
                "images": [],
                "prompt": "",
                "models": models_json,
                "cur_model_name": cur_model_name,
                "global_prompt": global_prompt,
                "negative_prompt": negative_prompt,
            },
        )

    prompt = request.form["prompt"]
    negative_prompt = request.form["negative_prompt"]
    n_iter = request.form["n_iter"]
    batch_size = request.form["batch_size"]
    width = request.form["width"]
    height = request.form["height"]
    steps = request.form["steps"]
    model = request.form["model"]

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
        response = http.post(url + "/sdapi/v1/txt2img", request_json)
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
                    "global_prompt": global_prompt,
                    "negative_prompt": negative_prompt,
                },
            )
    except Exception as e:
        logger.error(e)
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
                "global_prompt": global_prompt,
                "negative_prompt": negative_prompt,
            },
        )


@app.route("/cur_model")
def get_cur_model():
    url = request.args.get("url")
    opt_response = http.get(url + "/sdapi/v1/options")
    opt_json = opt_response.json()
    cur_hash = opt_json["sd_checkpoint_hash"][0:10]

    if "sd_model_checkpoint" in opt_json:
        cur_model = opt_json["sd_model_checkpoint"]
    else:
        cur_model = ""

    if "[" in cur_model and "]" in cur_model:
        cur_model_name = f"{cur_model}"
    else:
        cur_model_name = f"{cur_model} [{cur_hash}]"

    logger.info(f"当前的模型：{cur_model_name}")
    response = jsonify({"cur_model": cur_model_name})
    response.mimetype = "application/json"
    return response


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

        try:
            response = http.post(url + "/sdapi/v1/img2img", request_json)
            json_data = response.json()
            images = json_data.get("images", [])
            response = jsonify({"images": images})
            response.mimetype = "application/json"
            return response
        except Exception as e:
            logger.error(e)
            response = jsonify({"images": []})
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
    response = http.post(url + "/sdapi/v1/options", option_payload)

    if response.status_code == 200:
        return Response("success")
    else:
        return Response("failed")


@app.route("/test", methods=["GET", "POST"])
async def test_html():
    global result_urls
    global total
    global global_prompt
    global negative_prompt
    total = 0
    status = request.args.get("status")

    if result_urls is None or status == "refresh":
        logger.info("当前没有验证,重新获取喽!!!!")
        data = await read_json_files()
        timeout = aiohttp.ClientTimeout(sock_read=60)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            logger.info("-----------当前可用域名------------")
            tasks = []
            for item in data:
                task = asyncio.create_task(scan_port(session, item))
                tasks.append(task)
            result_urls = await asyncio.gather(*tasks)
            logger.info(f"-----------结束 {total}/{len(data)}------------")
    else:
        logger.info("有緩存，省事了")

    is_ajax_request = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if is_ajax_request:
        result = json.dumps(result_urls)
        return Response(result, mimetype="application/json")
    else:
        return render_template(
            "template.html",
            data={
                "list": result_urls,
                "total": len(result_urls),
                "allow": total,
                "global_prompt": global_prompt,
                "negative_prompt": negative_prompt,
            },
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
    visited_urls = set()
    for d in data:
        url = d["url"]
        if url not in visited_urls:
            unique_list.append(d)
            visited_urls.add(url)
    logger.info(f"总长度{len(data)} 去重后长度{len(unique_list)}")
    return unique_list


async def scan_port(session, item):
    global total
    global global_prompt
    api = item["url"] + "/sdapi/v1/txt2img"
    try:
        async with session.post(
            api,
            data=json.dumps(
                {
                    "n_iter": 4,
                    "width": 600,
                    "height": 800,
                    "prompt": global_prompt,
                    "negative_prompt": negative_prompt,
                }
            ),
            headers={"Content-Type": "application/json"},
        ) as response:
            if 200 <= response.status < 300:
                html_json = await response.json()
                images = html_json.get("images", [])
                if images[0] is not None:
                    total += 1
                    logger.info(item["url"])
                item["images"] = images
                return item
            else:
                return item
    except Exception:
        pass
    return item


if __name__ == "__main__":
    # app.run(port=9999)
    from waitress import serve

    MyLogger.clean_logs("logs", 3)
    logger.info("Server running at http://localhost:9999")
    serve(app, host="localhost", port=9999, threads=100)
