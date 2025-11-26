import string
import random
from datetime import datetime


def generate_random_str(prefix="zdh", length=8, use_lowercase=True, use_digit=True):
    """
    生成指定前缀（默认zdh）的随机字符串（前缀+随机部分，总长度可控）
    :param prefix: 固定前缀（默认"zdh"）
    :param length: 字符串总长度（默认8，需≥前缀长度，否则自动调整为前缀长度+1）
    :param use_lowercase: 是否包含小写字母（默认True）
    :param use_digit: 是否包含数字（默认True）
    :return: 带前缀的随机字符串（格式：前缀+随机字符）
    """
    # 校验前缀合法性（避免空前缀或特殊字符，可选）
    if not isinstance(prefix, str) or len(prefix.strip()) == 0:
        raise ValueError("前缀必须是非空字符串")

    # 调整总长度：确保总长度 ≥ 前缀长度（至少前缀+1位随机字符）
    min_total_length = len(prefix) + 1
    if length < min_total_length:
        print(f"警告：总长度{length}小于最小要求{min_total_length}，自动调整为{min_total_length}")
        length = min_total_length

    # 1. 组装字符集（根据参数选择是否包含小写字母/数字）
    char_set = ""
    if use_lowercase:
        char_set += string.ascii_lowercase
    if use_digit:
        char_set += string.digits

    # 校验：确保字符集不为空（避免参数错误导致无法生成）
    if not char_set:
        raise ValueError("至少需要启用一种字符类型（小写字母/数字）")

    # 2. 计算随机部分的长度（总长度 - 前缀长度）
    random_part_length = length - len(prefix)

    # 3. 生成随机部分（结合时间戳辅助去重，降低重复概率）
    timestamp_suffix = str(int(datetime.now().timestamp()))[-4:]  # 时间戳后4位
    # 随机部分 = 基础随机字符 + 时间戳后缀（确保随机性和唯一性）
    base_random = ''.join(random.choice(char_set) for _ in range(max(random_part_length - 4, 1)))  # 基础随机字符（至少1位）
    random_part = (base_random + timestamp_suffix)[:random_part_length]  # 截取到需要的长度

    # 4. 拼接前缀和随机部分，返回结果
    result = prefix + random_part
    return result[:length]  # 最终校验总长度（防止极端情况）


# ------------------- 使用示例 -------------------
if __name__ == "__main__":
    # 示例1：默认配置（前缀zdh，总长度8 → zdh + 5位随机字符）
    default_str = generate_random_str()
    print("默认（zdh+8位总长度）：", default_str)  # 示例：zdh3k728、zdh9d512 等

    # 示例2：自定义总长度（前缀zdh，总长度10 → zdh + 7位随机字符）
    custom_len_str = generate_random_str(length=10)
    print("zdh+10位总长度：", custom_len_str)  # 示例：zdha9x2k37、zdh8zq4592 等

    # 示例3：只包含小写字母（无数字）
    letter_only_str = generate_random_str(use_digit=False, length=9)
    print("zdh+9位（仅小写字母）：", letter_only_str)  # 示例：zdhxyzkjw、zdhabcdefg 等

    # 示例4：自定义前缀（如"test"）+ 总长度12
    custom_prefix_str = generate_random_str(prefix="test", length=12)
    print("test+12位总长度：", custom_prefix_str)  # 示例：test3k7289x45、test9d512abcde 等