import string
import random
from datetime import datetime  # 用于辅助避免重复（可选）


def generate_random_str(length=5, use_lowercase=True, use_digit=True):
    """
    生成指定长度的随机字符串（默认5位，小写字母+数字）
    :param length: 字符串长度（默认5）
    :param use_lowercase: 是否包含小写字母（默认True）
    :param use_digit: 是否包含数字（默认True）
    :return: 随机字符串
    """
    # 1. 组装字符集（根据参数选择是否包含小写字母/数字）
    char_set = ""
    if use_lowercase:
        char_set += string.ascii_lowercase
    if use_digit:
        char_set += string.digits

    # 校验：确保字符集不为空（避免参数错误导致无法生成）
    if not char_set:
        raise ValueError("至少需要启用一种字符类型（小写字母/数字）")

    # 2. 生成随机字符串（结合当前时间戳辅助去重，降低重复概率）
    # 时间戳转字符串后取后4位，与随机字符拼接，进一步减少重复
    timestamp_suffix = str(int(datetime.now().timestamp()))[-4:]
    # 随机部分的长度 = 总长度 - 时间戳后缀长度（确保总长度符合要求）
    random_part_length = max(length - len(timestamp_suffix), 1)  # 至少1位随机字符
    random_part = ''.join(random.choice(char_set) for _ in range(random_part_length))

    # 拼接随机部分和时间戳后缀，返回结果
    result = random_part + timestamp_suffix
    return result[:length]  # 确保最终长度严格符合要求（防止极端情况）


# ------------------- 使用示例 -------------------
if __name__ == "__main__":
    # 生成默认的5位小写+数字随机字符串
    default_str = generate_random_str()
    print("默认5位随机字符串：", default_str)  # 示例：x7283、9d512 等

    # 生成8位小写+数字的随机字符串（自定义长度）
    custom_len_str = generate_random_str(length=8)
    print("8位随机字符串：", custom_len_str)  # 示例：a9x2k371、8zq45926 等
