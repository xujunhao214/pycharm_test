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
DATETIME_ENDTIME = future_time.strftime("%Y-%m-%d")

# mysql查询语句，查询最近时间的数据
MYSQL_TIME = 1  # 时间范围（分钟）
WAIT_TIMEOUT = 30  # 数据库查询等待超时时间（秒）
DELETE_WAIT_TIMEOUT = 5  # 数据库删除查询超时时间（秒）
POLL_INTERVAL = 2  # 轮询间隔（秒）
STBLE_PERIOD = 3  # 稳定期（秒）：数据连续3秒不变则认为加载完成
TIMEZONE_OFFSET = 5  # 时区偏移量（小时）

# 执行完等待时间
SLEEP_SECONDS = 2

# redis的数据
SERVER = "39.99.136.49"
NODE = "FXAdamantStone-Real"
MFA_SECRET_KEY = "APVHUYXFWW4DZWT7L4HI3EO4Y7VY4J2VEXE4JGZNAVCYRSAOVNQQ"

# VPS的白名单
WHITE_LIST = ["6", "91", "22", "49"]
