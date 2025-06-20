import datetime

import pymysql

# VAR/VAR.py
# URL
# test测试环境
BASE_URL = 'http://39.99.136.49:9000'
VPS_URL = "http://39.99.136.49:9001"

# 数据库配置信息
DB_CONFIG = {
    "host": "39.99.136.49",  # 数据库服务器 IP
    "port": 3306,  # 数据库端口（整数类型）
    "user": "root",  # 数据库用户名
    "password": "xizcJWmXFkB5f4fm",  # 数据库密码
    "database": "follow-order-cp",  # 要连接的数据库名
    "charset": "utf8mb4",  # 字符集（支持中文及特殊字符）
    "cursorclass": pymysql.cursors.DictCursor,  # 返回字典格式结果，便于字段访问
    "connect_timeout": 10  # 连接超时时间（秒），防止长时间阻塞
}

# 账号列表-新增用户
USER_SERVER = "FXAdamantStone-Demo"
USER_SERVERNODE = "47.83.21.167:443"
ACCOUNT = "119999305"
ACCOUNTPASS = "e7cbbb0676452f88754c56852844abc8"

# 飞书机器人WEBHOOK_URL
WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/8d3475ac-8adc-45ed-97c7-0f0ec8647a4f"

# Jenkins路径
JENKINS = "http://39.108.0.84:8080/job/Documentatio_Test/"
JENKINS_USERNAME = "admin"
JENKINS_PASSWORD = "admin"

# 跟单平台账号密码
USERNAME = "admin"
PASSWORD = "04739db02172e04f63f5278211184deec745bad9d797882b343e7201898d8da1d9fced282f6b271d3815a5057482e62c6f6b88dacb642ba05632bd2ee348101c76cb1f86b70f91695fd1cff11fce76246f044ace477cdbfa1e3e1521b19b023b14c7165e82c5"

# 时间
DATETIME_NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# ------------------
# 服务器管理
# ------------------
# 服务器名称
SERVERNAME = "ceshi"
SERVERNAME_SEARCH = "103"
# 服务器节点
SERVERNODE = "103.35.116.124:443"

# 服务器IP
IPADDRESS = "127.0.0.1"
# 获取当前时间
current_time = datetime.datetime.now()
# 计算15天后的时间
future_time = current_time + datetime.timedelta(days=15)
# 格式化为指定字符串格式
DATETIME_ENDTIME = future_time.strftime("%Y-%m-%d %H:%M:%S")
