import time

import requests


class MyHttp:

    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    def set_headers(self, json):
        self.headers = json

    def get(self, url):
        start_time = time.time()
        response = requests.get(url, headers=self.headers)
        end_time = time.time()
        response_time = end_time - start_time
        print(f"{url}请求响应时间：{response_time} 秒")
        return response

    def post(self, url, json):
        start_time = time.time()
        response = requests.post(
            url, json=json, headers=self.headers
        )
        end_time = time.time()
        response_time = end_time - start_time
        print(f"{url}请求响应时间：{response_time} 秒")
        return response
