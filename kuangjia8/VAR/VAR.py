import pymysql

# VAR/VAR.py
# test测试环境
# URL

BASE_URL = 'http://39.99.136.49:9000'

# 数据库配置信息
DB_CONFIG = {
    "host": "39.99.136.49",  # 数据库服务器 IP
    "port": 3306,  # 数据库端口（整数类型）
    "user": "root",  # 数据库用户名
    "password": "xizcJWmXFkB5f4fm",  # 数据库密码
    "database": "information_schema",  # 要连接的数据库名
    "charset": "utf8mb4",  # 字符集（支持中文及特殊字符）
    "cursorclass": pymysql.cursors.DictCursor,  # 返回字典格式结果，便于字段访问
    "connect_timeout": 10  # 连接超时时间（秒），防止长时间阻塞
}

# 飞书机器人WEBHOOK_URL
WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/8d3475ac-8adc-45ed-97c7-0f0ec8647a4f"

# Jenkins路径
JENKINS = "http://39.108.0.84:8080/"
JENKINS_USERNAME = "admin"
JENKINS_PASSWORD = "admin"

# conftest.py 中导入
from kuangjia5.VAR.VAR import DB_CONFIG
