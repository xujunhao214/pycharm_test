from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64


# 加密函数
def aes_encrypt(plaintext: str, key: str, iv: str) -> str:
    key_bytes = key.encode('utf-8')
    iv_bytes = iv.encode('utf-8')
    plaintext_bytes = plaintext.encode('utf-8')
    padded_data = pad(plaintext_bytes, AES.block_size)
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
    encrypted_bytes = cipher.encrypt(padded_data)
    return base64.b64encode(encrypted_bytes).decode('utf-8')


# 解密函数（带格式修复）
def aes_decrypt(ciphertext_base64: str, key: str, iv: str) -> str:
    # 清理非 Base64 字符
    allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
    cleaned = ''.join([c for c in ciphertext_base64 if c in allowed_chars])

    # 补充填充符
    pad_count = len(cleaned) % 4
    if pad_count:
        cleaned += '=' * (4 - pad_count)

    # 解码
    try:
        ciphertext_bytes = base64.b64decode(cleaned, validate=True)
    except base64.binascii.Error as e:
        raise ValueError(f"无效的 Base64 数据: {e}")

    # 解密
    key_bytes = key.encode('utf-8')
    iv_bytes = iv.encode('utf-8')
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
    decrypted_bytes = cipher.decrypt(ciphertext_bytes)
    unpadded_data = unpad(decrypted_bytes, AES.block_size)
    return unpadded_data.decode('utf-8')


# 测试（使用已知有效的数据）
if __name__ == "__main__":
    key = '5fghiobv34534cldfgdfgdf2scvcbcfd'  # 32字节密钥
    iv = 'iovbjkdhjdfhfndk'  # 16字节IV

    # 测试1：用Python加密后解密（验证自身逻辑）
    test_plaintext = "测试加密解密"
    encrypted = aes_encrypt(test_plaintext, key, iv)
    print(f"加密后: {encrypted}")
    decrypted = aes_decrypt(encrypted, key, iv)
    print(f"解密后: {decrypted}")  # 应输出 "测试加密解密"

    # # 测试2：使用JavaScript加密的密文（替换为实际从JS获取的密文）
    # js_encrypted = "从JavaScript复制的密文"  # 例如 "U2FsdGVkX1..."
    # if js_encrypted:
    #     try:
    #         js_decrypted = aes_decrypt(js_encrypted, key, iv)
    #         print(f"JS密文解密后: {js_decrypted}")
    #     except Exception as e:
    #         print(f"JS密文解密失败: {e}")