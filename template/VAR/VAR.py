import datetime
import time

# 飞书机器人WEBHOOK_URL
WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/8d3475ac-8adc-45ed-97c7-0f0ec8647a4f"

# Jenkins路径
JENKINS = "http://39.108.0.84:8080/job/Documentatio_Test/"
JENKINS_USERNAME = "admin"
JENKINS_PASSWORD = "admin"

# 优化时间格式：
# DATETIME_NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")[:-3]
DATETIME_NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 获取当前时间
current_time = datetime.datetime.now()
# 计算15天后的时间
future_time = current_time + datetime.timedelta(days=30)
# 格式化为指定字符串格式
DATETIME_ENDTIME = future_time.strftime("%Y-%m-%d")

# 计算1小时前的时间（timedelta(hours=1) 表示1小时间隔）
one_hour_ago = current_time - datetime.timedelta(hours=1)

# 格式化为 "%Y-%m-%d %H:%M:%S"（与你当前 DATETIME_NOW 格式一致）
ONE_HOUR_AGO = one_hour_ago.strftime("%Y-%m-%d %H:%M:%S")

# mysql查询语句，查询最近时间的数据
MYSQL_TIME = 1  # 时间范围（分钟）
WAIT_TIMEOUT = 30  # 数据库查询等待超时时间（秒）
DELETE_WAIT_TIMEOUT = 5  # 数据库删除查询超时时间（秒）
POLL_INTERVAL = 2  # 轮询间隔（秒）
STBLE_PERIOD = 2  # 稳定期（秒）：数据连续2秒不变则认为加载完成
TIMEZONE_OFFSET = 5  # 时区偏移量（小时）

# api基类执行完等待时间
SLEEP_SECONDS = 3

# 项目名称
PROJECT_NAME = "跟单社区"

# 生成当前时间的毫秒级时间戳
current_timestamp_ms = int(time.time() * 1000)

# 生成当前时间的秒级时间戳
current_timestamp_seconds = int(time.time())

# 返佣管理-跟单分红查询日期
dividendTime_now = datetime.datetime.now().strftime("%Y-%m-%d")
dividendTime_ago = datetime.datetime.now() - datetime.timedelta(days=3)
dividendTime_ago = dividendTime_ago.strftime("%Y-%m-%d")

# 跟单社区
URL_TOP = "https://dev.lgcopytrade.top/api"
