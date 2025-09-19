import time
from template_model.commons.api_base import APITestBase, CompareOp, logger
import allure
import logging
import logging
import datetime
import re
import pytest
import requests
from template_model.VAR.VAR import *
from template_model.commons.jsonpath_utils import *
from template_model.commons.random_generator import *
from template_model.commons.session import percentage_to_decimal


@allure.feature("跟随方式-按手数")
class Test_openandclouseall(APITestBase):
    # 实例化JsonPath工具类（全局复用）
    json_utils = JsonPathUtils()

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("跟单管理-VPS管理-跟单者账号-开仓后")
    def test_query_openfollow_getRecordList(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            follow_account = var_manager.get_variable("follow_account")
            vpsrunIpAddr = var_manager.get_variable("vpsrunIpAddr")
            params = {
                "_t": current_timestamp_seconds,
                "pageNo": "1",
                "pageSize": "50",
                "accountLike": follow_account,
                "serverNameLike": "",
                "connectTraderLike": "",
                "connected": "",
                "runIpAddr": vpsrunIpAddr
            }
            response = self.send_get_request(
                logged_session,
                '/blockchain/account/getRecordList',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.searchCount",
                True,
                "响应searchCount字段应为true"
            )

        with allure.step(f"3. 数据校验"):
            with allure.step("跟单手数校验-MT4开仓手数和持仓订单手数"):
                totalLots = self.json_utils.extract(response.json(), "$.records[0].totalLots")
                logging.info(f"手数是: {totalLots}")

                lots_open = var_manager.get_variable("lots_open")

                follow_fixed_proportion = var_manager.get_variable("follow_fixed_proportion")
                follow_fixed_decimal = percentage_to_decimal(follow_fixed_proportion)
                expected_lots_open = lots_open * follow_fixed_decimal

                # 最小手数限制（0.01）
                min_order_size = 0.01
                if expected_lots_open < min_order_size:
                    allure.attach(
                        f"计算预期手数{expected_lots_open} < 最小手数{min_order_size}，强制重置为{min_order_size}",
                        "预期手数调整说明", allure.attachment_type.TEXT)
                    expected_lots_open = min_order_size

                self.verify_data(
                    actual_value=float(totalLots),
                    expected_value=float(expected_lots_open),
                    op=CompareOp.EQ,
                    message=f"手数符合预期",
                    attachment_name="手数详情"
                )
                logger.info(f"跟单者手数：{totalLots} MT4开仓手数：{expected_lots_open}")