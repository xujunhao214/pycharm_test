from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import binascii


class AESCrypto:
    def __init__(self, key: str, iv: str = None, mode=AES.MODE_CBC):
        """
        初始化AES加密解密器
        :param key: 密钥
        :param iv: 初始化向量(可选)
        :param mode: 加密模式，默认为CBC
        """
        self.key = key.encode('utf-8')
        self.mode = mode

        # 如果提供了IV，则使用它；否则为加密生成随机IV
        if iv:
            self.iv = iv.encode('utf-8')
        else:
            self.iv = None

    def encrypt(self, plaintext: str, iv: bytes = None) -> str:
        """
        加密方法
        :param plaintext: 明文
        :param iv: 可选的IV(用于解密时使用相同的IV)
        :return: 加密后的Base64字符串
        """
        # 如果未提供IV，则使用初始化时的IV或生成随机IV
        if iv is None:
            if self.iv:
                iv = self.iv
            else:
                # 生成随机IV
                import os
                iv = os.urandom(16)

        cipher = AES.new(self.key, self.mode, iv)
        plaintext_bytes = plaintext.encode('utf-8')
        padded_data = pad(plaintext_bytes, AES.block_size)
        encrypted_bytes = cipher.encrypt(padded_data)

        # 如果使用了随机IV，将IV附加到密文前面
        if self.iv is None:
            encrypted_bytes = iv + encrypted_bytes

        return base64.b64encode(encrypted_bytes).decode('utf-8')

    def decrypt(self, ciphertext: str) -> str:
        """
        解密方法
        :param ciphertext: 加密后的Base64字符串
        :return: 解密后的明文
        """
        ciphertext_bytes = base64.b64decode(ciphertext)

        # 如果使用了随机IV，从密文前面提取IV
        if self.iv is None:
            iv = ciphertext_bytes[:16]
            ciphertext_bytes = ciphertext_bytes[16:]
        else:
            iv = self.iv

        cipher = AES.new(self.key, self.mode, iv)
        decrypted_bytes = cipher.decrypt(ciphertext_bytes)
        unpadded_data = unpad(decrypted_bytes, AES.block_size)
        return unpadded_data.decode('utf-8')

    @staticmethod
    def bytes_to_hex(b: bytes) -> str:
        """将字节转换为十六进制字符串"""
        return binascii.hexlify(b).decode('ascii')

    @staticmethod
    def hex_to_bytes(hex_str: str) -> bytes:
        """将十六进制字符串转换为字节"""
        return binascii.unhexlify(hex_str)


# 调试工具函数
def debug_encryption_comparison():
    """比较不同加密方式的结果"""
    KEY = '5fghiobv34534cldfgdfgdf2scvcbcfd'
    IV = 'iovbjkdhjdfhfndk'
    PLAINTEXT = "admin"

    # 情况1: 使用固定IV
    crypto_fixed_iv = AESCrypto(KEY, IV)
    encrypted_fixed = crypto_fixed_iv.encrypt(PLAINTEXT)
    print(f"固定IV加密结果: {encrypted_fixed}")

    # 情况2: 使用随机IV(标准做法)
    crypto_random_iv = AESCrypto(KEY)
    encrypted_random = crypto_random_iv.encrypt(PLAINTEXT)
    print(f"随机IV加密结果: {encrypted_random}")

    # 情况3: 使用随机IV但手动指定(用于测试)
    test_iv = b'\x01' * 16  # 测试用固定IV
    crypto_test_iv = AESCrypto(KEY)
    encrypted_test = crypto_test_iv.encrypt(PLAINTEXT, test_iv)
    print(f"测试IV加密结果: {encrypted_test}")

    # 尝试解密您提供的密文
    your_ciphertext = "04249036cd6959ae9917ef0ecd087ba74b0ce7673baeba0bba491213ce264aee1f4f4f92f61c4ea61a5e292124a332d922512f4d1ab632334eb2ce7187c79d894919b285545f0dec0d7af5b7e93936698c072ef37926a8287c7be98c8402cb124c2d4dad9330"

    try:
        # 尝试作为Base64解密
        decrypted_base64 = crypto_fixed_iv.decrypt(your_ciphertext)
        print(f"Base64解密结果: {decrypted_base64}")
    except Exception as e:
        print(f"Base64解密失败: {e}")

    try:
        # 尝试作为十六进制解密(先转换为Base64)
        ciphertext_bytes = AESCrypto.hex_to_bytes(your_ciphertext)
        ciphertext_base64 = base64.b64encode(ciphertext_bytes).decode('utf-8')
        decrypted_hex = crypto_fixed_iv.decrypt(ciphertext_base64)
        print(f"十六进制解密结果: {decrypted_hex}")
    except Exception as e:
        print(f"十六进制解密失败: {e}")


if __name__ == "__main__":
    # 运行调试比较
    debug_encryption_comparison()
