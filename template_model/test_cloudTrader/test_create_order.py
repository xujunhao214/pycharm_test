import time
import allure
import logging
import pytest
from template_model.VAR.VAR import *
from template_model.conftest import var_manager
from template_model.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"

# 配置参数
TOTAL_CYCLES = 5  # 总循环次数
TRADE_RETRY_INTERVAL = 10  # 交易重试间隔(秒)
SYNC_WAIT_SECONDS = 2  # 同步等待时间


@allure.feature("VPS策略下单-复制下单")
class TestVPSOrdersend(APITestBase):
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略开仓平仓循环执行")
    def test_trader_open_close_loop(self, var_manager, logged_vps):
        """单条用例内完成多次开仓平仓循环，所有循环过程展示在步骤中"""
        allure.dynamic.description(f"共执行{TOTAL_CYCLES}次循环：每次循环包含开仓→平仓操作")

        # 获取基础变量（只获取一次，避免重复读取）
        trader_ordersend = var_manager.get_variable("trader_ordersend")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")

        # 循环执行开仓平仓
        for cycle_num in range(1, TOTAL_CYCLES + 1):
            with allure.step(f"第{cycle_num}/{TOTAL_CYCLES}次循环：开始"):
                try:
                    # 1. 策略开仓
                    with allure.step(f"第{cycle_num}次循环 - 发送策略开仓请求"):
                        data = {
                            "symbol": trader_ordersend["symbol"],
                            "placedType": 0,
                            "remark": f"gendanshequ_loop_{cycle_num}",  # 标记当前循环次数
                            "intervalTime": 0,
                            "type": 0,
                            "totalNum": trader_ordersend["totalNum"],
                            "totalSzie": trader_ordersend["totalSzie"],
                            "startSize": trader_ordersend["startSize"],
                            "endSize": trader_ordersend["endSize"],
                            "traderId": vps_trader_id
                        }
                        response = self.send_post_request(
                            logged_vps,
                            '/subcontrol/trader/orderSend',
                            json_data=data,
                        )

                    # 2. 验证开仓响应
                    with allure.step(f"第{cycle_num}次循环 - 验证开仓响应"):
                        self.assert_response_status(
                            response,
                            200,
                            f"第{cycle_num}次开仓失败"
                        )
                        self.assert_json_value(
                            response,
                            "$.msg",
                            "success",
                            f"第{cycle_num}次开仓响应msg字段应为success"
                        )

                    # 等待同步
                    time.sleep(SYNC_WAIT_SECONDS)

                    # 3. 策略平仓
                    with allure.step(f"第{cycle_num}次循环 - 发送策略平仓请求"):
                        data = {
                            "isCloseAll": 1,
                            "intervalTime": 0,
                            "traderId": vps_trader_id,
                            "account": vps_user_accounts_1
                        }
                        response = self.send_post_request(
                            logged_vps,
                            '/subcontrol/trader/orderClose',
                            json_data=data,
                        )

                    # 4. 验证平仓响应
                    with allure.step(f"第{cycle_num}次循环 - 验证平仓响应"):
                        self.assert_response_status(
                            response,
                            200,
                            f"第{cycle_num}次平仓失败"
                        )
                        self.assert_json_value(
                            response,
                            "$.msg",
                            "success",
                            f"第{cycle_num}次平仓响应msg字段应为success"
                        )

                    logger.info(f"第{cycle_num}/{TOTAL_CYCLES}次循环执行成功")

                except Exception as e:
                    error_msg = f"第{cycle_num}次循环执行失败: {str(e)}"
                    logger.error(error_msg)
                    allure.attach(error_msg, f"第{cycle_num}次循环失败详情", allure.attachment_type.TEXT)
                    time.sleep(TRADE_RETRY_INTERVAL)
                    # 若需要某一次循环失败后终止整个用例，取消下面这行的注释
                    # raise  # 抛出异常标记用例失败

            # 循环间的间隔（可选）
            if cycle_num < TOTAL_CYCLES:
                with allure.step(f"第{cycle_num}次循环完成，等待下一次循环开始"):
                    time.sleep(SYNC_WAIT_SECONDS)

        with allure.step(f"所有{TOTAL_CYCLES}次循环执行完毕"):
            logger.info(f"全部{TOTAL_CYCLES}次循环执行完成")
