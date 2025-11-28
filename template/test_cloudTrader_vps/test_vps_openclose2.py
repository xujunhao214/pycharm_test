import time
import allure
import logging
import pytest
from template.VAR.VAR import *
from template.conftest import var_manager
from template.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"

# 配置参数
TOTAL_CYCLES = 50  # 总循环次数
TRADE_RETRY_INTERVAL = 10  # 交易重试间隔(秒)
SYNC_WAIT_SECONDS = 2  # 同步等待时间


@allure.feature("VPS策略下单-复制下单")
class TestVPSOrdersend(APITestBase):
    # 生成循环参数（明确指定参数名称和范围）
    loop_params = [({"cycle_num": i + 1}) for i in range(TOTAL_CYCLES)]

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略开仓平仓循环执行")
    # 使用明确的参数名称进行参数化，避免歧义
    @pytest.mark.parametrize("params", loop_params)
    def test_trader_open_close_loop(self, var_manager, logged_vps, params):
        """开仓后平仓，循环执行50次（修复cycle字段报错）"""
        cycle_num = params["cycle_num"]  # 从参数中获取循环次数
        allure.dynamic.description(f"第{cycle_num}/{TOTAL_CYCLES}次循环：开仓→平仓")

        try:
            # 1. 策略开仓
            with allure.step(f"1. 第{cycle_num}次：发送策略开仓请求"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                vps_trader_id = var_manager.get_variable("vps_trader_id")
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
            with allure.step(f"2. 第{cycle_num}次：验证开仓响应"):
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
            with allure.step(f"3. 第{cycle_num}次：发送策略平仓请求"):
                vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
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
            with allure.step(f"4. 第{cycle_num}次：验证平仓响应"):
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
            allure.attach(error_msg, "循环执行失败详情", allure.attachment_type.TEXT)
            time.sleep(TRADE_RETRY_INTERVAL)
            raise  # 抛出异常标记用例失败
