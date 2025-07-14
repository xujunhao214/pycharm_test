from typing import Union
from gmssl.sm3 import sm3_hash

RS_LEN = 32
SM2_CURVE_NAME = "sm2p256v1"



def sm3_digest_hex(data: Union[str, bytes]) -> str:
    if isinstance(data, str):
        data = data.encode('utf-8')
    return sm3_hash([i for i in data])


if __name__ == '__main__':
    hash_result = sm3_digest_hex("admin")
    print(f"加密后: {hash_result}")