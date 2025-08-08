# lingkuan_801UAT/config.py
# 导入已有的Environment枚举（无需重复定义）
from lingkuan_801UAT.commons.enums import Environment
import pymysql

# 环境配置（仅保留配置数据，依赖现有枚举）
# 环境配置
ENV_CONFIG = {
    Environment.TEST: {
        "base_url": "https://uat.atcp.top/api",
        "vps_url": "https://39.99.145.155/vps",
        "db_config": {
            "host": "39.99.241.16",
            "port": 3306,
            "user": "root",
            "password": "5v07DqL!F7333",
            "database": "follow-order-cp",
            "charset": "utf8mb4",
            "cursorclass": pymysql.cursors.DictCursor,
            "connect_timeout": 10
        },
        "redis_config": {
            "host": "r-8vb1a249o1w1q605bppd.redis.zhangbei.rds.aliyuncs.com",
            "port": 6379,
            "db": 2,
            "password": "diVMn9bMpACrXh79QyYY"
        },
        "data_source_dir": "lingkuan_801UAT/VAR"
    },
    Environment.PROD: {
        "base_url": "https://uat.atcp.top/api",
        "vps_url": "https://39.99.145.155/vps",
        "db_config": {
            "host": "39.99.241.16",
            "port": 3306,
            "user": "root",
            "password": "5v07DqL!F7333",
            "database": "follow-order-cp",
            "charset": "utf8mb4",
            "cursorclass": pymysql.cursors.DictCursor,
            "connect_timeout": 10
        },
        "redis_config": {
            "host": "r-8vb1a249o1w1q605bppd.redis.zhangbei.rds.aliyuncs.com",
            "port": 6379,
            "db": 2,
            "password": "diVMn9bMpACrXh79QyYY"
        },
        "data_source_dir": "lingkuan_801UAT/VAR"
    },
    "data_source_dir": "lingkuan_801UAT/VAR"
}
