# lingkuan_UAT/commons/redis_utils.py
import redis
import json
from typing import Dict, Any, List, Optional
from lingkuan_UAT.config import ENV_CONFIG  # 导入配置数据
from lingkuan_UAT.commons.enums import Environment  # 导入现有枚举


class RedisClient:
    def __init__(self, host: str, port: int, db: int, password: Optional[str] = None):
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


# 新增：解析Decimal/BigDecimal格式的工具函数
def parse_decimal_value(value: Any) -> Any:
    """解析可能是Java BigDecimal或Decimal格式的值（如 [\"java.math.BigDecimal\", \"3.99\"]）"""
    if isinstance(value, list) and len(value) == 2 and value[0] == 'java.math.BigDecimal':
        return float(value[1])  # 转换为浮点数便于比较
    return value  # 非特定格式则直接返回


def get_redis_client(environment: Environment) -> RedisClient:
    redis_config = ENV_CONFIG[environment]["redis_config"]
    return RedisClient(
        host=redis_config["host"],
        port=redis_config["port"],
        db=redis_config["db"],
        password=redis_config["password"]
    )


def convert_redis_orders_to_comparable_list(redis_orders: List[Dict]) -> List[Dict]:
    """将Redis订单数据转换为与数据库结果一致的可比较格式"""
    comparable_list = []
    for order in redis_orders:
        # 映射Redis字段到数据库字段（根据实际数据库表结构调整）
        comparable_list.append({
            "order_no": order["ticket"],  # 假设数据库字段名为ticket
            "magical": order["magic"],  # 假设数据库字段名为magic
            "size": order["lots"],  # 假设数据库字段名为lots
            "open_price": order["openPrice"],  # 假设数据库字段名为open_price
            "symbol": order["symbol"]  # 假设数据库字段名为symbol
        })
    return comparable_list
