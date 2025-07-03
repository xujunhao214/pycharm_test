import datetime

# 飞书机器人WEBHOOK_URL
WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/8d3475ac-8adc-45ed-97c7-0f0ec8647a4f"

# Jenkins路径
JENKINS = "http://39.108.0.84:8080/job/Documentatio_Test/"
JENKINS_USERNAME = "admin"
JENKINS_PASSWORD = "admin"

# 优化时间格式：
DATETIME_NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 获取当前时间
current_time = datetime.datetime.now()
# 计算15天后的时间
future_time = current_time + datetime.timedelta(days=15)
# 格式化为指定字符串格式
DATETIME_ENDTIME = future_time.strftime("%Y-%m-%d %H:%M:%S")

# mysql查询语句，查询最近时间的数据
MYSQL_TIME = 1
WAIT_TIMEOUT = 30  # 统一等待超时时间（秒）
POLL_INTERVAL = 2  # 轮询间隔（秒）
