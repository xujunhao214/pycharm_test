import hashlib
import json


def generate_sign(app_key, authorization, platform, timestamp, body, secret):
    """生成签名"""
    sign_content = f"AppKey{app_key}Authorization{authorization}Platform{platform}Timestamp{timestamp}"

    # 如果body非空，则将body json序列化并拼接到后面
    if body is not None:
        sign_content += json.dumps(body, separators=(',', ':'))  # 使用紧凑格式，无空格

    # 将secret拼接到signContent后面
    sign_content += secret

    # 将signContent全部转为小写
    sign_content = sign_content.lower()

    # 用MD5对signContent进行处理
    md5 = hashlib.md5()
    md5.update(sign_content.encode('utf-8'))

    return md5.hexdigest()
