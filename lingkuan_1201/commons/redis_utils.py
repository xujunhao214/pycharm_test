# lingkuan_1201/commons/redis_utils.py
import redis
import json
from typing import Dict, Any, List
from lingkuan_1201.config import ENV_CONFIG  # 导入配置数据
from lingkuan_1201.commons.enums import Environment  # 导入现有枚举


class RedisClient:
    def __init__(self, host: str, port: int, db: int, password: str = None):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.client = self._connect()

    def _connect(self) -> redis.Redis:
        """创建Redis连接"""
        try:
            return redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=False  # 先不自动解码，后续手动处理二进制
            )
        except redis.RedisError as e:
            raise ConnectionError(f"Redis连接失败: {str(e)}")

    def get_hash_data(self, key: str) -> Dict[str, Any]:
        """获取哈希类型数据并解析（二进制转字符串/JSON）"""
        try:
            data = self.client.hgetall(key)
            if not data:
                return {}

            parsed_data = {}
            for field, value in data.items():
                # 解析字段名（二进制转字符串）
                field_str = field.decode('utf-8')
                # 解析值（尝试JSON反序列化，失败则保留字符串）
                try:
                    value_str = value.decode('utf-8')
                    value_obj = json.loads(value_str)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    value_obj = value_str if 'value_str' in locals() else value.decode('utf-8', errors='ignore')
                parsed_data[field_str] = value_obj
            return parsed_data
        except redis.RedisError as e:
            raise RuntimeError(f"获取Redis哈希数据失败 (key={key}): {str(e)}")

    def close(self):
        """关闭Redis连接"""
        self.client.close()


def get_redis_client(environment: Environment) -> RedisClient:
    redis_config = ENV_CONFIG[environment]["redis_config"]
    return RedisClient(
        host=redis_config["host"],
        port=redis_config["port"],
        db=redis_config["db"],
        password=redis_config["password"]
    )


def convert_redis_orders_to_comparable_list(redis_orders: List[Dict]) -> List[Dict]:
    comparable_list = []
    for order in redis_orders:
        comparable_list.append({
            "order_no": order["ticket"],  # Redis ticket → 统一字段order_no
            "magical": order["magic"],  # Redis magic → 统一字段magical
            "size": order["lots"],  # Redis lots → 统一字段size
            "open_price": order["openPrice"],
            "symbol": order["symbol"]
        })
    return comparable_list
