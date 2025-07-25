import redis
import json

REDIS_CONFIG = {
    'host': 'r-8vb1a249o1w1q605bppd.redis.zhangbei.rds.aliyuncs.com',
    'port': 6379,
    'db': 1,
    'password': 'diVMn9bMpACrXh79QyYY'
}


def get_redis_data():
    r = redis.Redis(**REDIS_CONFIG)  # 使用 Redis 替代 StrictRedis
    key = "follow:repair:send:39.99.136.49#FXAdamantStone-Real#FXAdamantStone-Real#300140#300142"

    try:
        data = r.hgetall(key)
        if data:
            # 解析二进制数据为字典
            parsed_data = {}
            for field, value in data.items():
                field_str = field.decode('utf-8')
                # 尝试解析为 JSON，如果失败则保留原始字符串
                try:
                    value_obj = json.loads(value.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    value_obj = value.decode('utf-8', errors='ignore')
                parsed_data[field_str] = value_obj

            return parsed_data
        else:
            print(f"Key {key} 不存在或为空")
            return None
    except redis.RedisError as e:
        print(f"Redis错误: {e}")
        return None


def parse_redis_data(redis_data):
    results = []

    for key, value in redis_data.items():
        if isinstance(value, list) and len(value) >= 2 and value[0] == 'net.maku.followcom.pojo.EaOrderInfo':
            order_data = value[1]
            if isinstance(order_data, dict):
                results.append({
                    'ticket': order_data.get('ticket'),
                    'magic': order_data.get('magic'),
                    'lots': order_data.get('lots'),
                    'profit': parse_decimal_value(order_data.get('profit')),
                    'openPrice': order_data.get('openPrice'),
                    'symbol': order_data.get('symbol')
                })

    return results


def parse_decimal_value(value):
    """解析可能是 BigDecimal 格式的值"""
    if isinstance(value, list) and len(value) == 2 and value[0] == 'java.math.BigDecimal':
        return float(value[1])
    return value


if __name__ == "__main__":
    redis_data = get_redis_data()
    if redis_data:
        orders = parse_redis_data(redis_data)
        for order in orders:
            print(f"订单 {order['ticket']}:")
            print(f"  Magic: {order['magic']}")
            print(f"  Lots: {order['lots']}")
            print(f"  Profit: {order.get('profit', 'N/A')}")
            print(f"  Symbol: {order.get('symbol', 'N/A')}")
            print("-" * 30)
