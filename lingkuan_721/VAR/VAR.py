import datetime

# 加密密钥
MT4 = "FOLLOWERSHIP4KEY"
PASSWORD = "Test123456"

# 飞书机器人WEBHOOK_URL
WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/8d3475ac-8adc-45ed-97c7-0f0ec8647a4f"

# Jenkins路径
JENKINS = "http://39.108.0.84:8080/job/Documentatio_Test/"
JENKINS_USERNAME = "admin"
JENKINS_PASSWORD = "admin"

# 优化时间格式：
DATETIME_NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")[:-3]

# 获取当前时间
current_time = datetime.datetime.now()
# 计算15天后的时间
future_time = current_time + datetime.timedelta(days=30)
# 格式化为指定字符串格式
DATETIME_ENDTIME = future_time.strftime("%Y-%m-%d %H:%M:%S")

# mysql查询语句，查询最近时间的数据
MYSQL_TIME = 1  # 时间范围（分钟）
WAIT_TIMEOUT = 30  # 数据库查询等待超时时间（秒）
DELETE_WAIT_TIMEOUT = 5  # 数据库删除查询超时时间（秒）
POLL_INTERVAL = 2  # 轮询间隔（秒）
STBLE_PERIOD = 3  # 稳定期（秒）：数据连续3秒不变则认为加载完成

# redis的数据
SERVER = "39.99.136.49"
NODE = "FXAdamantStone-Real"
MFA_SECRET_KEY = "APVHUYXFWW4DZWT7L4HI3EO4Y7VY4J2VEXE4JGZNAVCYRSAOVNQQ"
import datetime

# 加密密钥
MT4 = "FOLLOWERSHIP4KEY"
PASSWORD = "Test123456"

# 飞书机器人WEBHOOK_URL
WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/8d3475ac-8adc-45ed-97c7-0f0ec8647a4f"

# Jenkins路径
JENKINS = "http://39.108.0.84:8080/job/Documentatio_Test/"
JENKINS_USERNAME = "admin"
JENKINS_PASSWORD = "admin"

# 优化时间格式：
DATETIME_NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")[:-3]

# 获取当前时间
current_time = datetime.datetime.now()
# 计算15天后的时间
future_time = current_time + datetime.timedelta(days=30)
# 格式化为指定字符串格式
DATETIME_ENDTIME = future_time.strftime("%Y-%m-%d %H:%M:%S")

# mysql查询语句，查询最近时间的数据
MYSQL_TIME = 1  # 时间范围（分钟）
WAIT_TIMEOUT = 30  # 数据库查询等待超时时间（秒）
DELETE_WAIT_TIMEOUT = 5  # 数据库删除查询超时时间（秒）
POLL_INTERVAL = 2  # 轮询间隔（秒）
STBLE_PERIOD = 3  # 稳定期（秒）：数据连续3秒不变则认为加载完成

# redis的数据
SERVER = "39.99.136.49"
NODE = "FXAdamantStone-Real"
MFA_SECRET_KEY = "APVHUYXFWW4DZWT7L4HI3EO4Y7VY4J2VEXE4JGZNAVCYRSAOVNQQ"

# VPS的白名单
WHITE_LIST = [
    1, 52, 53, 54, 55, 56, 57, 58, 59, 60,
    61, 62, 63, 64, 65, 66, 67, 68, 69, 70,
    72, 73, 74, 75, 76, 77, 78, 79, 80, 81,
    82, 83, 84, 85, 86, 87, 88, 89, 90, 91,
    191, 192, 193, 194, 195, 196, 197, 198, 199, 200,
    201, 204
]
