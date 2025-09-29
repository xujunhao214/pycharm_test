# template_model/config.py
# 导入已有的Environment枚举（无需重复定义）
from template_model.commons.enums import Environment
import pymysql

# 环境配置（仅保留配置数据，依赖现有枚举）
# 环境配置
ENV_CONFIG = {
    Environment.TEST: {
        "base_url": "https://dev.lgcopytrade.top/api",
        "vps_url": "http://39.99.136.49/vps",
        "db_config": {
            "host": "39.99.146.95",
            "port": 3306,
            "user": "root",
            "password": "gQ9^sR7#tD5j",
            "database": "copyglobal_v2_schema",
            "charset": "utf8mb4",
            "cursorclass": pymysql.cursors.DictCursor,
            "connect_timeout": 10
        },
        "redis_config": {
            "host": "r-8vb1a249o1w1q605bppd.redis.zhangbei.rds.aliyuncs.com",
            "port": 6379,
            "db": 1,
            "password": "diVMn9bMpACrXh79QyYY"
        },
        "data_source_dir": "template_model/VAR"
    },
    Environment.UAT: {
        "base_url": "https://dev.lgcopytrade.top/api",
        "vps_url": "https://39.101.181.190/vps",
        "db_config": {
            "host": "39.99.146.95",
            "port": 3306,
            "user": "root",
            "password": "gQ9^sR7#tD5j",
            "database": "copyglobal_v2_schema",
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
        "data_source_dir": "template_model/VAR"
    }
}
