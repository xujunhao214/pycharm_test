#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/2/13 16:43
# @Author  : Cyj
# @File    : mfa_key.py
# @Software: PyCharm
# @synopsis: 获取MFA验证码

import base64
import hashlib
import hmac
import logging
import time as sys_time


def add_padding(secret):
    """自动为Base32密钥添加填充符"""
    padding = '=' * (8 - len(secret) % 8) if len(secret) % 8 != 0 else ''
    return secret + padding


def generate_code(secret):
    """根据已有密钥生成当前时间的验证码"""
    secret = add_padding(secret)  # 自动添加填充符
    decoded_key = base64.b32decode(secret)  # 解码密钥

    # 获取当前时间，单位为秒，按30秒为周期
    t = int(sys_time.time() // 30)

    # 将时间戳转换为8字节数组
    data = bytearray(8)
    for i in range(8):
        data[7 - i] = (t >> (i * 8)) & 0xff

    # 使用 HMAC-SHA1 生成哈希值
    mac = hmac.new(decoded_key, data, hashlib.sha1)
    hash_bytes = mac.digest()

    # 动态截断
    offset = hash_bytes[19] & 0x0f
    truncated_hash = 0
    for i in range(4):
        truncated_hash = (truncated_hash << 8) | (hash_bytes[offset + i] & 0xff)

    truncated_hash = truncated_hash & 0x7fffffff  # 取低31位
    truncated_hash = truncated_hash % 1000000  # 生成6位验证码

    return truncated_hash


if __name__ == '__main__':
    # 使用提供的密钥
    secret_key = 'UD53WUTCFMTHXGTKETHP5BTEFWH3DMFF6NHQXDR5DI4H4T4GUEAGVOMFFKAO6KT2NEQZ2KUBPVEYTP5QOTDEFHIDSH5QGDZKTDRC34A'
    code = generate_code(secret_key)
    print(code)
    logging.info(f"{code}")