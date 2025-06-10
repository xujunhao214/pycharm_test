from datetime import datetime, timedelta
import time


def get_current_timestamp():
    """获取当前时间戳（毫秒级）"""
    return str(int(time.time() * 1000))


def get_today_start_end_timestamp():
    """获取今日开始和结束时间的时间戳（毫秒级）"""
    now = datetime.now()

    # 今日开始时间: 00:00:00
    today_start = datetime(now.year, now.month, now.day)
    start_timestamp = int(today_start.timestamp() * 1000)

    # 今日结束时间: 23:59:59
    today_end = today_start + timedelta(days=1, seconds=-1)
    end_timestamp = int(today_end.timestamp() * 1000)

    return start_timestamp, end_timestamp
