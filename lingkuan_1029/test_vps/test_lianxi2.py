import time
import math
import random
import allure
import logging
import pytest
from lingkuan_1029.VAR.VAR import *
from lingkuan_1029.conftest import var_manager
from lingkuan_1029.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"

# 全局中断标志：用于检测到 Trade timeout 时终止所有执行
GLOBAL_STOP_FLAG = False


@allure.feature("VPS策略下单-开仓的场景校验")
class TestVPSOrdersendbuy:
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSOrderSend1(APITestBase):
        # 用 fixture 动态生成50组测试数据（循环索引+随机type），避免类级变量时机问题
        @pytest.fixture(scope="class", params=[(i, random.choice([0, 1])) for i in range(50)])
        def loop_params(self, request):
            """动态生成循环参数：(loop_idx, type_val)，执行50次，每次随机type=0/1"""
            return request.param

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略开仓（循环{loop_idx}次，type={type_val}）")
        def test_trader_orderSend(self, loop_params, class_random_str, var_manager, logged_session):
            global GLOBAL_STOP_FLAG
            loop_idx, type_val = loop_params  # 从fixture获取循环索引和type值

            # 若全局中断标志已触发，直接跳过当前及后续用例
            if GLOBAL_STOP_FLAG:
                pytest.skip("前序循环检测到 Trade timeout，中断所有执行")

            logger.info(f"===== 开始第 {loop_idx + 1}/50 次循环开仓，type={type_val} =====")
            data = {
                "type": type_val,  # 使用随机生成的type（0或1）
                "intervalTime": 0,
                "symbol": "EURUSD",
                "startSize": "0.01",
                "endSize": "0.01",
                "totalNum": "30",
                "totalSzie": "",
                "remark": class_random_str,
                "traderId": 15427
            }
            response = self.send_post_request(
                logged_session,
                '/subcontrol/trader/orderSend',
                json_data=data,
            )

            # 验证响应状态码和内容
            self.assert_response_status(
                response,
                200,
                f"第 {loop_idx + 1} 次循环策略开仓失败"
            )
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                f"第 {loop_idx + 1} 次循环响应msg字段应为success"
            )
            logger.info(f"第 {loop_idx + 1} 次循环开仓成功，等待60秒...")
            time.sleep(60)

        ACCOUNT_LIST = [
            "40003281",
            "39685",
            "73159",
            "702091",
            "777837",
            "851246",
            "3583722",
            "7362738",
            "9850258",
            "66939933",
            "591001087"
        ]

        @pytest.mark.parametrize("account", ACCOUNT_LIST)
        @allure.title("数据库校验-策略开仓-指令及订单详情数据检查（循环{loop_idx}次）")
        def test_dbquery_orderSend(self, loop_params, class_random_str, var_manager, db_transaction, account):
            global GLOBAL_STOP_FLAG
            loop_idx, type_val = loop_params  # 从fixture获取循环索引

            # 若全局中断标志已触发，直接跳过
            if GLOBAL_STOP_FLAG:
                pytest.skip("前序循环检测到 Trade timeout，中断所有执行")

            logger.info(f"===== 开始第 {loop_idx + 1}/50 次循环数据库校验 =====")
            with allure.step("1. 获取订单详情表账号数据"):
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
                        fod.send_no,
                        fod.magical,
                        fod.remark,
                        fod.open_price,
                        fod.symbol,
                        fod.order_no,
                        foi.true_total_lots,
                        foi.order_no,
                        foi.operation_type,
                        foi.create_time,
                        foi.status,
                        foi.min_lot_size,
                        foi.max_lot_size,
                        foi.total_lots,
                        foi.total_orders
                    FROM 
                        follow_order_detail fod
                    INNER JOIN 
                        follow_order_instruct foi 
                    ON 
                        foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                    WHERE foi.operation_type = %s
                        AND fod.account = %s
                        AND fod.comment = %s
                    """
                params = (
                    '0',
                    account,
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail(f"第 {loop_idx + 1} 次循环数据库查询结果为空，订单可能没有入库")

                remark = db_data[0]["remark"]
                if remark == "Trade timeout":
                    logger.error(f"第 {loop_idx + 1} 次循环检测到 Trade timeout，触发全局中断！")
                    GLOBAL_STOP_FLAG = True  # 设置全局标志，中断后续所有循环
                    pytest.fail(f"第 {loop_idx + 1} 次循环订单已超时，中断所有执行")

            logger.info(f"第 {loop_idx + 1} 次循环数据库校验通过")

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略平仓（循环{loop_idx}次）")
        def test_trader_orderclose(self, loop_params, class_random_str, var_manager, logged_session):
            global GLOBAL_STOP_FLAG
            loop_idx, type_val = loop_params  # 从fixture获取循环索引

            # 若全局中断标志已触发，直接跳过
            if GLOBAL_STOP_FLAG:
                pytest.skip("前序循环检测到 Trade timeout，中断所有执行")

            logger.info(f"===== 开始第 {loop_idx + 1}/50 次循环平仓 =====")
            data = {
                "flag": 0,
                "intervalTime": 0,
                "symbol": "EURUSD",
                "closeType": 2,
                "remark": "",
                "type": 2,
                "traderId": 15427,
                "account": "40003281"
            }
            response = self.send_post_request(
                logged_session,
                '/subcontrol/trader/orderClose',
                json_data=data,
            )

            # 验证响应
            self.assert_response_status(
                response,
                200,
                f"第 {loop_idx + 1} 次循环平仓失败"
            )
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                f"第 {loop_idx + 1} 次循环平仓响应msg字段应为success"
            )
            logger.info(f"第 {loop_idx + 1} 次循环平仓成功，等待20秒...")
            time.sleep(20)

    # 重置全局标志（避免多次运行时状态残留）
    @classmethod
    def teardown_class(cls):
        global GLOBAL_STOP_FLAG
        GLOBAL_STOP_FLAG = False
        logger.info("===== 所有循环执行完毕，重置全局中断标志 =====")
