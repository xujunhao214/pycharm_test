#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    常量统一管理文件，为了方便代码中迅速识别
    目录、文件、常量名全大写
"""

# 公共参数
HEADERS = {
    "city": "0755"
}

"""
客服管理后台：
链接：https://api-c.ebk365.com:26887/b
"""
# 项目链接
PROJCET_URL = "https://api-c.ebk365.com:26887/b"
# 正确的用户名
USERNAME = "ebike"
# 正确的密码密码
PASSWD = "c33367701511b4f6020ec61ded352059"

"""
微信小程序：
链接：https://api-c.ebk365.com:26888/api
"""

PROJCET_URL_Weixin = "https://api-c.ebk365.com:26888/api"

TOKEN_WeiXin = "eyJhbGciOiJIUzI1NiJ9.eyJqdGkiOiI4MDc4NTEiLCJpYXQiOjE3MTc3NTEwMjcsInN1YiI6IiIsImlzcyI6IiIsImF1ZCI6IjBhZjVhZmY2LTFhODEtNDAzMy04ZTVjLTgxODQ2Yjg1YzhlNCIsImV4cCI6MTcxODYxNTAyN30.RFefdMtnA3QFB_sZvnOrA6CYDiZhh9A0dCuGYrw2_zA"

"""
维修工：
链接：https://api-c.ebk365.com:26886/r
"""
PROJCET_URL_WORKER = "https://api-c.ebk365.com:26886/r"

TOKEN_WEIXIU = "eyJhbGciOiJIUzM4NCJ9.eyJyYW5kb21LZXkiOiJmYWI0MTJlMS0wYjk3LTRmMmMtOGM3Ni02MzAzNzk5NDQ4ZTkiLCJyZXBhaXJlcklkIjo2LCJleHBpcmVUaW1lIjoxNzIwNzc3MDA1MDUyLCJsb2dpblRpbWUiOjE3MTgxODUwMDUwNTIsIm5pY2tuYW1lIjoi5rWL6K-VODE4MyIsImlhdCI6MTcxODE4NTAwNX0.zMV9Pgp6roZaMc_p_7w3dxDF1xEHpInXR6Bl4WeAzqOQKcEhiXOotuhgFaKsMj2T"

# headers的值：
# 假设您有以下变量值（请替换为实际值）
import time

app_key = "apiFox"
platform = "apiFox"
secret = "53c8eae1c4e4ecd5adb66a6b8b47a45f"
# 获取当前时间戳（转换为毫秒级）
timestamp = str(int(time.time() * 1000))
# print(timestamp)

# 获取今日开始结束时间的时间戳
from dateutil import parser
import datetime

now = datetime.datetime.now()
time_day = now.strftime('%Y-%m-%d')
print(time_day)

date_str = str(time_day) + " 00:00:00"
print(date_str)
dt = parser.parse(date_str)
timestamp_start = round(dt.timestamp()) * 1000
print("时间戳：", timestamp_start)

date_str2 = str(time_day) + " 23:59:59"
dt2 = parser.parse(date_str2)
timestamp_end = round(dt2.timestamp()) * 1000
print("时间戳：", timestamp_end)

"""
门店后台：https://api-c.ebk365.com:26887/b/shop/auth/login
"""
SHOP_URL = "https://api-c.ebk365.com:26887/b"
SHOP_name = "13616510214"
SHOP_password = "1ef70db0a7669ce2f89e78fb2eaab0f9"
