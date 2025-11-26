import time
from template1126.commons.api_base import APITestBase, CompareOp, logger
import allure
import logging
import logging
import datetime
import re
import pytest
import requests
from template1126.VAR.VAR import *
from template1126.commons.jsonpath_utils import *
from template1126.commons.random_generator import *
from template1126.commons.session import percentage_to_decimal
from template1126.public_function.proportion_public import PublicUtils


@allure.feature("跟随方式-按手数")
class Test_numberall:
    @allure.story("场景1：跟随方式-按手数-0.01")
    @allure.description("""
    ### 测试说明
    - 前置条件：有喊单账号、跟单账号，跟单已经和喊单有订阅关系
      1. 修改订阅信息，跟随方式-按手数-0.01
      2. 自研跟单-VPS策略账号进行开仓，总手数0.01
      3. 账号管理-持仓订单-喊单和跟单数据校验
      4. 跟单管理-开仓日志-喊单和跟单数据校验
      5. 跟单管理-VPS管理-喊单和跟单数据校验
      6. 自研跟单-VPS策略账号进行平仓
      7. 账号管理-持仓订单-喊单和跟单数据校验
      8. 账号管理-历史订单-喊单和跟单数据校验
      9. 跟单管理-开仓日志-喊单和跟单数据校验
      10.跟单管理-VPS管理-喊单和跟单数据校验
    - 预期结果：喊单和跟单数据校验正确
    """)
    # @pytest.mark.skipif(True, reason="跳过此用例")
    class Test_orderseng1(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("账号管理-历史订单-喊单MT4账户查询-平仓后")
        def test_query_trader_id(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_pass_id = var_manager.get_variable("trader_pass_id")
                trader_account = var_manager.get_variable("trader_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "trader_id": trader_pass_id,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 20,
                    "superQueryMatchType": "and"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/402883977b38c9ca017b38c9d0960001',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step(f"3. 查询校验"):
                order_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                logging.info(f"喊单者手数是: {order_size}")
                var_manager.set_runtime_variable("order_size", order_size)

                trader_id_list = self.json_utils.extract(
                    response.json(),
                    "$.result.records[0].trader_id",
                    default=[],
                    multi_match=True
                )

                if not trader_id_list:
                    attach_body = f"MT4账号查询[{trader_account}]，返回的trader_id列表为空（暂无数据）"
                else:
                    attach_body = f"MT4账号查询[{trader_account}]，返回 {len(trader_id_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"账号ID:{trader_account}查询结果",
                    attachment_type="text/plain"
                )

                for idx, trader_id in enumerate(trader_id_list):
                    self.verify_data(
                        actual_value=int(trader_id),
                        expected_value=int(trader_pass_id),
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的账号ID应为{trader_id}",
                        attachment_name=f"账号ID:{trader_pass_id}第 {idx + 1} 条记录校验"
                    )

                    with allure.step("订单号校验"):
                        order_no = self.json_utils.extract(response.json(), "$.result.records[0].order_no")
                        ticket_open = var_manager.get_variable("ticket_open")

                        self.verify_data(
                            actual_value=order_no,
                            expected_value=ticket_open,
                            op=CompareOp.EQ,
                            use_isclose=False,
                            message=f"订单号数据应符合预期",
                            attachment_name="订单号详情"
                        )
                        logger.info(f"订单号数据应符合预期,开仓订单号：{ticket_open} 喊单者订单号：{order_no}")

                    with allure.step("喊单手数校验-开仓手数和持仓订单手数"):
                        order_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                        logging.info(f"喊单者手数是: {order_size}")

                        lots_open = var_manager.get_variable("lots_open")
                        self.verify_data(
                            actual_value=float(order_size),
                            expected_value=float(lots_open),
                            op=CompareOp.EQ,
                            message=f"手数应符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"喊单者手数：{order_size} 开仓手数：{lots_open}")
