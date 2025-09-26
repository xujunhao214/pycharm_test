import datetime

# 加密密钥
MT4 = "FOLLOWERSHIP4KEY"
PASSWORD = "Test123456"

# 飞书机器人WEBHOOK_URL
WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/8d3475ac-8adc-45ed-97c7-0f0ec8647a4f"

# Jenkins路径
JENKINS = "http://172.96.192.137:8080/view/%E8%87%AA%E5%8A%A8%E5%8C%96%E6%B5%8B%E8%AF%95/job/QA-copytrade-uat/"
JENKINS_USERNAME = "Test"
JENKINS_PASSWORD = "28y6yyrcnfE3WSxF"

# 优化时间格式：
DATETIME_NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")[:-3]

# 获取当前时间
current_time = datetime.datetime.now()
# 计算15天后的时间
future_time = current_time + datetime.timedelta(days=30)
# 格式化为指定字符串格式
DATETIME_ENDTIME = future_time.strftime("%Y-%m-%d")

# mysql查询语句，查询最近时间的数据
MYSQL_TIME = 1.5  # 时间范围（分钟）
WAIT_TIMEOUT = 30  # 数据库查询等待超时时间（秒）
DELETE_WAIT_TIMEOUT = 5  # 数据库删除查询超时时间（秒）
POLL_INTERVAL = 2  # 轮询间隔（秒）
STBLE_PERIOD = 2  # 稳定期（秒）：数据连续2秒不变则认为加载完成
TIMEZONE_OFFSET = 5  # 时区偏移量（小时）

# api基类执行完等待时间
SLEEP_SECONDS = 1

# MFA登录生成新的验证码秘钥
MFA_SECRET_KEY = "APVHUYXFWW4DZWT7L4HI3EO4Y7VY4J2VEXE4JGZNAVCYRSAOVNQQ"

# 项目名称
PROJECT_NAME = "自研跟单V1.4.2"

# MT4URL
MT4_URL = "https://mt4.mtapi.io"
