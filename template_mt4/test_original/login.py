import requests
from template_mt4.commons.jsonpath_utils import *
from template_mt4.commons.captcha import *
import time
import json
from template_mt4.VAR.VAR import *

url = f"https://dev.lgcopytrade.top/api/sys/randomImage/{current_timestamp_ms}?_t={current_timestamp_seconds}"

payload = {}
headers = {
    'priority': 'u=1, i',
    'tenant_id': '0',
    'x-sign': '417B110F1E71BD2CFE96366E67849B0B',
    'X-Access-Token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NTc0OTMyMDMsInVzZXJuYW1lIjoiYWRtaW4ifQ.PkFLjsBa0NbCUF8ROtmIGABzYmUH2ldQfqz_ERvaKsY',
    'Accept': '*/*',
    'Host': 'dev.lgcopytrade.top',
    'Connection': 'keep-alive'
}

response = requests.request("GET", url, data=payload)
json_utils = JsonPathUtils()
result = json_utils.extract(response.json(), "$.result")
print(result)
recognizer = UniversalCaptchaRecognizer()
result_base64 = recognizer.adaptive_recognize(result)
print(result_base64)

url = "https://dev.lgcopytrade.top/api/sys/login"
data = {
    "username": "xujunhao@163.com",
    "password": "123456",
    "remember_me": "true",
    "captcha": result_base64,  # 验证码Base64
    "checkKey": f"{current_timestamp_ms}"  # 时间戳参数
}

# 关键修复：使用 json 参数而非 data 参数，自动处理JSON序列化
response = requests.request("POST", url, json=data)

# 提取code字段
result2 = json_utils.extract(response.json(), "$.message")
print("响应code：", result2)

# 打印完整JSON响应
all_json_data = response.json()
print("完整响应数据：")
print(json.dumps(all_json_data, indent=2, ensure_ascii=False))
