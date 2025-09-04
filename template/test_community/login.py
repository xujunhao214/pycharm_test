import requests
from template.commons.jsonpath_utils import *
from template.commons.captcha import *

url = "https://dev.lgcopytrade.top/api/sys/randomImage/1756888731743?_t=1756888731"

payload = {}
headers = {
    'priority': 'u=1, i',
    'tenant_id': '0',
    'x-sign': '417B110F1E71BD2CFE96366E67849B0B',
    'x-timestamp': '20250903163851',
    'X-Access-Token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NTc0OTMyMDMsInVzZXJuYW1lIjoiYWRtaW4ifQ.PkFLjsBa0NbCUF8ROtmIGABzYmUH2ldQfqz_ERvaKsY',
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    'Accept': '*/*',
    'Host': 'dev.lgcopytrade.top',
    'Connection': 'keep-alive'
}

response = requests.request("GET", url, headers=headers, data=payload)
json_utils = JsonPathUtils()
result = json_utils.extract(response.json(), "$.result")
print(result)

result_base64 = recognize_captcha_base64(result)
print(result_base64)

# url = "https://dev.lgcopytrade.top/api/sys/login"
#
# payload = "{\"username\":\"xujunhao@163.com\",\"password\":\"123456\",\"remember_me\":true,\"captcha\":\"zzaj\",\"checkKey\":1756888824729}"
# headers = {
#    'priority': 'u=1, i',
#    'tenant_id': '0',
#    'X-Access-Token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NTc0OTMyMDMsInVzZXJuYW1lIjoiYWRtaW4ifQ.PkFLjsBa0NbCUF8ROtmIGABzYmUH2ldQfqz_ERvaKsY',
#    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
#    'content-type': 'application/json;charset=UTF-8',
#    'Accept': '*/*',
#    'Host': 'dev.lgcopytrade.top',
#    'Connection': 'keep-alive'
# }
#
# response = requests.request("POST", url, headers=headers, data=payload)
#
# print(response.text)
