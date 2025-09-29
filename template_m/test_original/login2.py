import requests
from template_model.commons.jsonpath_utils import JsonPathUtils
from template_model.commons.captcha import UniversalCaptchaRecognizer
import time
import json
from template_model.VAR.VAR import *

# 初始化工具类
json_utils = JsonPathUtils()
recognizer = UniversalCaptchaRecognizer()


def get_new_captcha():
    """
    获取新的验证码（包含Base64和对应的checkKey时间戳）
    返回：(captcha_base64, check_key) 验证码Base64字符串 + 时间戳（用于登录参数）
    """
    # 1. 生成新的时间戳（每次获取验证码必须用新时间戳，避免缓存）
    current_timestamp_ms = int(time.time() * 1000)  # 毫秒级（用于checkKey和URL）
    current_timestamp_seconds = int(time.time())  # 秒级（用于URL的_t参数）

    # 2. 发送GET请求获取验证码
    captcha_url = f"https://dev.lgcopytrade.top/api/sys/randomImage/{current_timestamp_ms}?_t={current_timestamp_seconds}"
    captcha_headers = {
        'priority': 'u=1, i',
        'tenant_id': '0',
        'x-sign': '417B110F1E71BD2CFE96366E67849B0B',
        # 注意：获取验证码通常不需要X-Access-Token（登录前令牌可能无效），可根据实际接口调整
        # 'X-Access-Token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NTc0OTMyMDMsInVzZXJuYW1lIjoiYWRtaW4ifQ.PkFLjsBa0NbCUF8ROtmIGABzYmUH2ldQfqz_ERvaKsY',
        'Accept': '*/*',
        'Host': 'dev.lgcopytrade.top',
        'Connection': 'keep-alive'
    }

    try:
        captcha_response = requests.get(captcha_url, headers=captcha_headers, timeout=5)
        captcha_response.raise_for_status()  # 若状态码非200，抛出异常
        captcha_json = captcha_response.json()

        # 3. 提取验证码Base64（从result字段）
        captcha_base64 = json_utils.extract(captcha_json, "$.result")
        if not captcha_base64:
            print("[获取验证码失败] 未提取到Base64数据")
            return None, None

        recognizer = UniversalCaptchaRecognizer()
        result_base64 = recognizer.adaptive_recognize(captcha_base64)
        print(result_base64)

        # 4. 识别验证码（调用你的验证码识别逻辑）
        recognized_code = recognizer.adaptive_recognize(captcha_base64)
        print(f"[获取验证码成功] 识别结果：{recognized_code}，checkKey：{current_timestamp_ms}")
        return recognized_code, current_timestamp_ms  # 返回识别结果和对应的时间戳

    except Exception as e:
        print(f"[获取验证码异常] {str(e)}")
        return None, None


def login_with_retry(max_retry=5, retry_interval=10):
    """
    带重试的登录逻辑：验证码错误时自动重新获取并重试
    参数：max_retry 最大重试次数
    返回：登录响应JSON（成功）/ None（多次失败）
    """
    retry_count = 0  # 重试计数器

    while retry_count < max_retry:
        # 1. 获取新的验证码和checkKey
        recognized_code, check_key = get_new_captcha()
        if not recognized_code or not check_key:
            retry_count += 1
            print(f"[登录重试] 验证码获取失败，{retry_interval}秒后重试（{retry_count}/{max_retry}）")
            time.sleep(retry_interval)  # 间隔10秒再重试，避免频繁请求
            continue

        # 2. 构造登录参数
        login_url = "https://dev.lgcopytrade.top/api/sys/login"
        login_data = {
            "username": "xujunhao@163.com",  # 建议从VAR中读取，如VAR.USERNAME
            "password": "123456",  # 建议从VAR中读取，如VAR.PASSWORD
            "remember_me": "true",
            "captcha": recognized_code,  # 识别后的验证码
            "checkKey": f"{check_key}"  # 与当前验证码对应的时间戳
        }
        login_headers = {
            'priority': 'u=1, i',
            'tenant_id': '0',
            'X-Access-Token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NTc0OTMyMDMsInVzZXJuYW1lIjoiYWRtaW4ifQ.PkFLjsBa0NbCUF8ROtmIGABzYmUH2ldQfqz_ERvaKsY',
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'content-type': 'application/json;charset=UTF-8',
            'Accept': '*/*',
            'Host': 'dev.lgcopytrade.top',
            'Connection': 'keep-alive'
        }

        try:
            # 3. 发送登录请求（使用json参数确保格式正确）
            login_response = requests.post(
                login_url,
                headers=login_headers,
                json=login_data,  # 关键：用json参数自动序列化
                timeout=5
            )
            login_response.raise_for_status()
            login_result = login_response.json()
            print(f"\n[登录请求结果] 第{retry_count + 1}次尝试：")
            print(json.dumps(login_result, indent=2, ensure_ascii=False))

            # 4. 判断登录结果
            if login_result.get("success") is True:
                print(f"[登录成功] 获取令牌：{login_result.get('result', {}).get('token')}")
                return login_result  # 登录成功，返回结果
            else:
                message = login_result.get("message", "未知错误")
                if "验证码错误" in message:
                    retry_count += 1
                    print(f"[登录失败] {message}，{retry_interval}秒后重试（{retry_count}/{max_retry}）")
                    time.sleep(retry_interval)  # 间隔1秒重试
                else:
                    # 非验证码错误（如账号密码错误），无需重试，直接返回
                    print(f"[登录失败] 非验证码错误：{message}，停止重试")
                    return login_result

        except Exception as e:
            retry_count += 1
            print(f"[登录异常] {str(e)}，{retry_interval}秒后重试（{retry_count}/{max_retry}）")
            time.sleep(retry_interval)

    # 超过最大重试次数
    print(f"\n[登录失败] 已尝试{max_retry}次，均因验证码错误或异常，停止重试")
    return None


# ---------------------- 执行登录 ----------------------
if __name__ == "__main__":
    login_result = login_with_retry(max_retry=5, retry_interval=10)
    # if login_result and login_result.get("success"):
    #     # 登录成功后的后续操作（如保存令牌到VAR）
    #     token = login_result.get("result", {}).get("token")
    #     if token:
    #         VAR.X_ACCESS_TOKEN = token  # 假设VAR中定义了X_ACCESS_TOKEN用于后续请求
    #         print(f"[后续操作] 令牌已保存：{token}")
