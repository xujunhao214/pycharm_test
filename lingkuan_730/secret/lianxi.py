from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64


class AESCrypto:
    def __init__(self, key: str, iv: str):
        """初始化AES加密解密器（密钥和IV与JS保持一致）"""
        if len(key) != 32:
            raise ValueError("AES-256需要32字节的密钥")
        if len(iv) != 16:
            raise ValueError("CBC模式需要16字节的IV")

        self.key = key.encode('utf-8')  # 密钥转字节
        self.iv = iv.encode('utf-8')  # IV转字节

    def encrypt(self, plaintext: str) -> str:
        """加密：创建独立的加密器对象"""
        # 每次加密都新建一个加密器（避免与解密冲突）
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        plaintext_bytes = plaintext.encode('utf-8')
        padded_data = pad(plaintext_bytes, AES.block_size)
        encrypted_bytes = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted_bytes).decode('utf-8')

    def decrypt(self, ciphertext: str) -> str:
        """解密：创建独立的解密器对象"""
        # 每次解密都新建一个解密器（避免与加密冲突）
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        ciphertext_bytes = base64.b64decode(ciphertext)
        decrypted_bytes = cipher.decrypt(ciphertext_bytes)
        unpadded_data = unpad(decrypted_bytes, AES.block_size)
        return unpadded_data.decode('utf-8')


# 使用示例
if __name__ == "__main__":
    KEY = '5fghiobv34534cldfgdfgdf2scvcbcfd'  # 32字节密钥
    IV = 'iovbjkdhjdfhfndk'  # 16字节IV

    crypto = AESCrypto(KEY, IV)

    # 加密
    plaintext = "admin"
    encryption = crypto.encrypt(plaintext)
    print(f"加密后: {encryption}")

    # 解密
    decode = crypto.decrypt("encryption")
    print(f"解密后: {decode}")

    # 验证一致性
    assert decode == plaintext, "加密解密结果不一致！"
    print("加密解密验证通过！")