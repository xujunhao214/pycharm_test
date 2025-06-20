from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import hashlib

# 明文、密钥（需确保密钥长度正确）
plaintext = "Qw123456"
key = "FOLLOWERSHIP4KEY".encode('utf-8')  # 转为字节

# 检查密钥长度（AES-128需16字节，AES-256需32字节）
if len(key) != 16:
    raise ValueError("密钥长度必须为16字节（AES-128）")

# 生成固定IV（用于CBC模式，需确保解密时使用相同IV）
iv = b'\x00' * 16  # 示例：固定IV，实际应使用随机值并随密文传输


# PKCS7填充函数
def pkcs7_pad(data, block_size=16):
    padding_length = block_size - (len(data) % block_size)
    padding = bytes([padding_length]) * padding_length
    return data + padding


# PKCS7去填充函数
def pkcs7_unpad(data):
    padding_length = data[-1]
    return data[:-padding_length]


# 定义加密函数
def encrypt(plaintext, key, iv):
    # 明文转为字节（需确保编码一致）
    plaintext_bytes = plaintext.encode('utf-8')

    # 应用PKCS7填充
    padded_data = pkcs7_pad(plaintext_bytes)

    # 创建密码器（AES-128-CBC模式）
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # 加密
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    # 转为十六进制字符串（便于对比）
    return ciphertext.hex()


# 定义解密函数
def decrypt(ciphertext, key, iv):
    # 十六进制字符串转字节
    ciphertext_bytes = bytes.fromhex(ciphertext)

    # 创建密码器
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    # 解密
    padded_plaintext = decryptor.update(ciphertext_bytes) + decryptor.finalize()

    # 去除PKCS7填充
    plaintext_bytes = pkcs7_unpad(padded_plaintext)

    # 转为字符串
    return plaintext_bytes.decode('utf-8')


# 执行加密
ciphertext = encrypt(plaintext, key, iv)
print("加密后:", ciphertext)

# 执行解密
decrypted = decrypt(ciphertext, key, iv)
print("解密后:", decrypted)

# 验证闭环
if decrypted == plaintext:
    print("✅ 加密-解密闭环验证成功")
else:
    print("❌ 验证失败")