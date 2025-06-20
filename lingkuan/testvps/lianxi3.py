import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


def zero_pad(data, block_size=16):
    """零填充：用0字节填充到块大小的整数倍"""
    padding_length = (-len(data)) % block_size
    return data + bytes([0]) * padding_length


def zero_unpad(data):
    """去除零填充"""
    return data.rstrip(b'\x00')


def aes_encrypt_ecb(key, plaintext):
    """使用ECB模式和零填充进行加密，严格匹配原Crypto库结果"""
    # 确保密钥是16字节（AES-128）
    key_bytes = key.encode('utf-8')
    if len(key_bytes) != 16:
        raise ValueError("密钥长度必须为16字节")

    # 明文需要用JSON序列化（添加引号）
    json_text = json.dumps(plaintext)
    data_bytes = json_text.encode('utf-8')

    # 应用零填充
    padded_data = zero_pad(data_bytes)

    # 创建ECB模式的密码器
    cipher = Cipher(
        algorithms.AES(key_bytes),
        modes.ECB(),
        backend=default_backend()
    )

    # 执行加密
    encryptor = cipher.encryptor()
    encrypted_bytes = encryptor.update(padded_data) + encryptor.finalize()

    # 转换为十六进制字符串
    return encrypted_bytes.hex()


def aes_decrypt_ecb(key, encrypted_hex):
    """使用ECB模式和零填充进行解密，严格匹配原Crypto库结果"""
    # 确保密钥是16字节
    key_bytes = key.encode('utf-8')
    if len(key_bytes) != 16:
        raise ValueError("密钥长度必须为16字节")

    # 将十六进制字符串转换为字节
    encrypted_bytes = bytes.fromhex(encrypted_hex)

    # 创建ECB模式的密码器
    cipher = Cipher(
        algorithms.AES(key_bytes),
        modes.ECB(),
        backend=default_backend()
    )

    # 执行解密
    decryptor = cipher.decryptor()
    decrypted_bytes = decryptor.update(encrypted_bytes) + decryptor.finalize()

    # 去除零填充
    unpadded_bytes = zero_unpad(decrypted_bytes)

    # 解析JSON字符串（去除引号）
    return json.loads(unpadded_bytes.decode('utf-8'))


# 示例用法
if __name__ == "__main__":
    MT4_KEY = "FOLLOWERSHIP4KEY"  # 16字节密钥
    password = "Qw123456"  # 明文

    # 加密
    encrypted = aes_encrypt_ecb(MT4_KEY, password)
    print("Encrypted:", encrypted)

    # 解密
    encrypted="12a42347e63122d3ce13a0dfd6ed9e12"
    decrypted = aes_decrypt_ecb(MT4_KEY, encrypted)
    print(f"Decrypted: {decrypted}")  # 必须输出 Qw123456
