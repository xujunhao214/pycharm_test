from gmssl import sm2, func

def generate_sm2_key_pair():
    """生成SM2密钥对（公钥65字节，私钥32字节）"""
    key_pair = sm2.CryptSM2().generate_key_pair()
    public_key = key_pair.public_key().export_key().hex()
    private_key = key_pair.private_key().export_key().hex()
    # 提取65字节公钥（04开头）和32字节私钥
    public_key_65 = public_key[2:]  # 去掉前缀，保留核心65字节
    private_key_32 = private_key
    return public_key_65, private_key_32

# 生成新密钥对
PUBLIC_KEY, PRIVATE_KEY = generate_sm2_key_pair()
print(f"新生成公钥（65字节）: {PUBLIC_KEY}")
print(f"新生成私钥（32字节）: {PRIVATE_KEY}")

# 验证密钥格式
def check_key(public, private):
    assert len(public) == 130 and public.startswith("04"), "公钥格式错误"
    assert len(private) == 64, "私钥格式错误"
    print("✅ 密钥格式正确")

check_key(PUBLIC_KEY, PRIVATE_KEY)

# 初始化SM2（C1C3C2模式）
sm2_crypt = sm2.CryptSM2(public_key=PUBLIC_KEY, private_key=PRIVATE_KEY, mode=1)

# 加解密函数
def encrypt(data):
    return sm2_crypt.encrypt(data.encode()).hex()

def decrypt(encrypted_hex):
    return sm2_crypt.decrypt(bytes.fromhex(encrypted_hex)).decode()

# 测试
if __name__ == "__main__":
    data = "admin"
    encrypted = encrypt(data)
    print(f"加密: {encrypted}")
    decrypted = decrypt(encrypted)
    print(f"解密: {decrypted}")
    assert decrypted == data, "加解密失败"
    print("✅ Python内部测试通过")