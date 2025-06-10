# Common/sign_utils.py
import hashlib
import json
import time
from typing import Dict


def generate_sign(app_key: str, authorization: str, platform: str, body: Dict = None, secret: str = None) -> str:
    """生成签名（解耦secret依赖）"""
    timestamp = str(int(time.time() * 1000))
    sign_content = f"AppKey{app_key}Authorization{authorization}Platform{platform}Timestamp{timestamp}"

    if body is not None:
        sign_content += json.dumps(body, ensure_ascii=False)  # 处理中文JSON
    if secret is None:
        from api_test_framework_refactor.VAR.VAR import secret  # 兜底导入（建议通过参数传递）
    sign_content += secret
    sign_content = sign_content.lower()

    md5 = hashlib.md5()
    md5.update(sign_content.encode('utf-8'))
    return md5.hexdigest(), timestamp
