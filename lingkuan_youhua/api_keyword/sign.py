import hashlib
import json


def sign(app_key: str, authorization: str, platform: str, timestamp: str, body: object, secret: str):
    signContent = "AppKey" + app_key + "Authorization" + authorization + "Platform" + platform + "Timestamp" + timestamp
    # 如果body非空空，则将body json序列化并拼接到后面
    if body is not None:
        signContent = signContent + json.dumps(body)
    # 将secret拼接到signContent后面
    signContent = signContent + secret
    # 将signContent全部转为小写
    signContent = signContent.lower()
    print(signContent)
    # 用MD5对signContent进行处理
    md5 = hashlib.md5()
    md5.update(signContent.encode('utf-8'))
    return md5.hexdigest()
