import json
import Crypto
from Crypto.Cipher import AES


def zero_pad(data, block_size):
    padding_length = (-len(data)) % block_size
    return data + bytes([0] * padding_length)


def zero_unpad(data):
    return data.rstrip(b'\x00')


def aes_encrypt_hex(mode, padding, key, content, salt=None, charset='utf-8'):
    json_str = json.dumps(content)
    data = json_str.encode(charset)
    key_bytes = key.encode(charset)
    iv_bytes = salt.encode(charset) if salt else None

    if mode == AES.MODE_ECB:
        cipher = AES.new(key_bytes, mode)
    else:
        if not iv_bytes:
            raise ValueError("IV/salt required for non-ECB modes")
        cipher = AES.new(key_bytes, mode, iv=iv_bytes)

    if padding == 'ZeroPadding':
        data = zero_pad(data, AES.block_size)
    elif padding == 'PKCS7':
        data = zero_pad(data, AES.block_size)
    else:
        raise ValueError("Unsupported padding")

    encrypted = cipher.encrypt(data)
    return encrypted.hex()


def aes_decrypt_hex(mode, padding, key, encrypt_hex, salt=None, charset='utf-8'):
    key_bytes = key.encode(charset)
    iv_bytes = salt.encode(charset) if salt else None
    encrypted = bytes.fromhex(encrypt_hex)

    if mode == AES.MODE_ECB:
        cipher = AES.new(key_bytes, mode)
    else:
        if not iv_bytes:
            raise ValueError("IV/salt required for non-ECB modes")
        cipher = AES.new(key_bytes, mode, iv=iv_bytes)

    decrypted = cipher.decrypt(encrypted)
    if padding == 'ZeroPadding':
        decrypted = zero_unpad(decrypted)
    elif padding == 'PKCS7':
        decrypted = zero_unpad(decrypted)

    return json.loads(decrypted.decode(charset))


def aes_encrypt_str(password, key):
    return aes_encrypt_hex(AES.MODE_ECB, 'ZeroPadding', key, password, None)


def decrypt_str(encrypted_hex, key):
    key_bytes = key.encode('utf-8')
    encrypted = bytes.fromhex(encrypted_hex)
    cipher = AES.new(key_bytes, AES.MODE_ECB)
    decrypted = zero_unpad(cipher.decrypt(encrypted))
    decrypted_str = decrypted.decode('utf-8')
    if decrypted_str[0] == '"' and decrypted_str[-1] == '"':
        decrypted_str = decrypted_str[1:-1]
    return decrypted_str


# 示例用法
if __name__ == "__main__":
    MT4_KEY = "FOLLOWERSHIP4KEY"
    # 加密
    password = "Qw123456"
    encrypted = aes_encrypt_str(password, MT4_KEY)
    print("Encrypted:", encrypted)

    # 解密
    password = '5b3fe6cb1acedfbda639a6b1236ec870'
    decrypted = decrypt_str(password, MT4_KEY)
    print("Decrypted:", decrypted)