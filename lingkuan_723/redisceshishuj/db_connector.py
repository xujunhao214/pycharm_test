# MySQL配置
MYSQL_CONFIG = {
    'user': 'root',
    'password': 'xizcJWmXFkB5f4fm',
    'host': '39.99.136.49',
    'database': 'follow-order-cp',
}

UAT_MYSQL_CONFIG = {
    'user': 'root',
    'password': '5v07DqL!F7333',
    'host': '39.99.241.16',
    'database': 'follow-order-cp',
}

# Redis配置
REDIS_CONFIG = {
    'host': 'r-8vb1a249o1w1q605bppd.redis.zhangbei.rds.aliyuncs.com',
    'port': 6379,
    'db': 1,
    'password': 'diVMn9bMpACrXh79QyYY'
}

# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/2/13 11:14
# @Author  : Cyj
# @File    : db_connector.py
# @Software: PyCharm
# @synopsis: 处理Redis与MySQL的连接


import pymysql  # 替换mysql.connector为pymysql
from lingkuan_723.redis import redis


# 获取MySQL连接（使用pymysql）
def get_mysql_connection():
    # pymysql.connect() 参数与mysql.connector兼容，直接传入配置字典即可
    return pymysql.connect(**MYSQL_CONFIG)


def get_uat_mysql_connection():
    return pymysql.connect(** UAT_MYSQL_CONFIG)


# 获取Redis连接（无需修改）
def get_redis_connection():
    return redis.StrictRedis(**REDIS_CONFIG)
