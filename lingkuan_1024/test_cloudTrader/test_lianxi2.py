import time
import math
import allure
import logging
import pytest
from lingkuan_1024.VAR.VAR import *
from lingkuan_1024.conftest import var_manager
from lingkuan_1024.commons.api_base import APITestBase
from lingkuan_1024.commons.redis_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


# ---------------------------
# 修改模式、品种
# ---------------------------
@allure.feature("云策略策略下单-跟单修改模式、品种")
class TestCloudOrderSend_Scence(APITestBase):
    @allure.title("出现漏开-redis数据和数据库的数据做比对")
    def test_dbquery_redis(self, var_manager, db_transaction, redis_cloudTrader_data_send):
        with allure.step("1. 获取订单详情表账号数据"):
            cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
            cloudOrderSend = var_manager.get_variable("cloudOrderSend")
            symbol = cloudOrderSend["symbol"]

            sql = f"""
                           SELECT * 
                           FROM follow_order_detail 
                           WHERE symbol LIKE %s 
                             AND account = %s
                             AND comment = %s
                           """
            params = (
                f"%{symbol}%",
                cloudTrader_user_accounts_2,
                "changjing1"
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.query_database_with_time(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time"
            )

        with allure.step("2. 转换Redis数据为可比较格式"):
            if not redis_cloudTrader_data_send:
                pytest.fail("Redis中未查询到订单数据")

            # 转换Redis数据为与数据库一致的格式
            cloudtrader_redis_comparable_openlist = convert_redis_orders_to_comparable_list(
                redis_cloudTrader_data_send)
            logging.info(f"转换后的Redis数据: {cloudtrader_redis_comparable_openlist}")

            # 将转换后的数据存入变量管理器
            var_manager.set_runtime_variable("cloudtrader_redis_comparable_openlist",
                                             cloudtrader_redis_comparable_openlist)

        with allure.step("3. 比较Redis与数据库数据"):
            # 假设db_data是之前从数据库查询的结果
            if not db_data:
                pytest.fail("数据库中未查询到订单数据")

            # 提取数据库中的关键字段（根据实际数据库表结构调整）
            db_comparable_list = [
                {
                    "order_no": record["order_no"],  # 数据库order_no → 统一字段order_no
                    "magical": record["magical"],  # 数据库magical → 统一字段magical
                    "size": float(record["size"]),  # 数据库size → 统一字段size
                    "open_price": float(record["open_price"]),
                    "symbol": record["symbol"]
                }
                for record in db_data
            ]
            logging.info(f"数据库转换后: {db_comparable_list}")
            # 比较两个列表（可根据需要调整比较逻辑）
            self.assert_data_lists_equal(
                actual=cloudtrader_redis_comparable_openlist,
                expected=db_comparable_list,
                fields_to_compare=["order_no", "magical", "size", "open_price", "symbol"],
                tolerance=1e-6
            )