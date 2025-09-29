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
from template_model.public_function.proportion_public import PublicUtils


@allure.feature("跟随方式-按净值")
class Test_equitall:
    @allure.story("场景1：跟随方式-按净值-100%")
    @allure.description("""
    ### 测试说明
    - 前置条件：有喊单账号、跟单账号，跟单已经和喊单有订阅关系
      1. 修改订阅信息，跟随方式-按净值-100%
      2. MT4进行登录，然后进行开仓，总手数0.01
      3. 账号管理-持仓订单-喊单和跟单数据校验
      4. 跟单管理-开仓日志-喊单和跟单数据校验
      5. 跟单管理-VPS管理-喊单和跟单数据校验
      6. MT4进行平仓
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
        @allure.title("跟单管理-实时跟单-修改订阅数据")
        def test_query_updata_editPa(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_jeecg_rowkey = var_manager.get_variable("follow_jeecg_rowkey")
                data = {
                    "id": follow_jeecg_rowkey,
                    "direction": "FORWARD",
                    "followingMode": 4,
                    "fixedProportion": 100,
                    "fixedLots": None
                }
                response = self.send_put_request(
                    logged_session,
                    '/blockchain/master-slave/editPa',
                    json_data=data
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-实时跟单-订阅列表数据")
        def test_query_getColumnsAndData(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_account = var_manager.get_variable("follow_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "account": follow_account,
                    "pageNo": "1",
                    "pageSize": "20",
                    "status": "NORMAL,AUDIT"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )
            with allure.step("3. 提取数据"):
                fixed_proportion = self.json_utils.extract(response.json(),
                                                           "$.result.data.records[0].fixed_proportion")
                var_manager.set_runtime_variable("fixed_proportion", fixed_proportion)

        @pytest.mark.retry(n=3, delay=10)
        @allure.title("跟单管理-VPS管理-提取喊单者净值")
        def test_query_get_traderquit(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_account = var_manager.get_variable("trader_account")
                vpsrunIpAddr = var_manager.get_variable("vpsrunIpAddr")
                params = {
                    "_t": current_timestamp_seconds,
                    "pageNo": "1",
                    "pageSize": "50",
                    "accountLike": trader_account,
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

            with allure.step(f"3. 提取净值数据"):
                trader_equity = self.json_utils.extract(response.json(), "$.records[0].equity")
                currency = self.json_utils.extract(response.json(), "$.records[0].currency")

                if currency == "USD":
                    trader_periodP = round(float(trader_equity) * 1.0, 2)
                elif currency == "JPY":
                    trader_periodP = round(float(trader_equity) * 0.00672, 2)
                elif currency == "AUD":
                    trader_periodP = round(float(trader_equity) * 0.6251, 2)
                elif currency == "USC":
                    trader_periodP = round(float(trader_equity) * 0.01, 2)
                else:
                    pytest.fail(f"不支持的币种：{currency}，请补充币种转换逻辑")

                logging.info(f"币种的转换详情,当前币种{currency}，转换前：{trader_equity},转换后：{trader_periodP}")
                allure.attach(f"当前币种{currency}，转换前：{trader_equity},转换后：{trader_periodP}",
                              "币种类型转换详情", allure.attachment_type.TEXT)
                var_manager.set_runtime_variable("trader_periodP", trader_periodP)

        @allure.title("跟单管理-VPS管理-提取跟单者净值")
        def test_query_get_followquit(self, var_manager, logged_session):
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

            with allure.step(f"3. 提取净值数据"):
                follow_equity = self.json_utils.extract(response.json(), "$.records[0].equity")
                currency = self.json_utils.extract(response.json(), "$.records[0].currency")

                if currency == "USD":
                    follow_periodP = round(float(follow_equity) * 1.0, 2)
                elif currency == "JPY":
                    follow_periodP = round(float(follow_equity) * 0.00672, 2)
                elif currency == "AUD":
                    follow_periodP = round(float(follow_equity) * 0.6251, 2)
                elif currency == "USC":
                    follow_periodP = round(float(follow_equity) * 0.01, 2)
                else:
                    pytest.fail(f"不支持的币种：{currency}，请补充币种转换逻辑")

                logging.info(f"币种的转换详情,当前币种{currency}，转换前：{follow_equity},转换后：{follow_periodP}")
                allure.attach(f"当前币种{currency}，转换前：{follow_equity},转换后：{follow_periodP}",
                              "币种类型转换详情", allure.attachment_type.TEXT)
                var_manager.set_runtime_variable("follow_periodP", follow_periodP)

        @allure.title("公共方法-校验前操作")
        def test_run_public(self, var_manager, logged_session):
            # 实例化类
            public_front = PublicUtils()

            # 按顺序调用
            # 登录获取 token
            public_front.test_login(var_manager)
            # 平仓喊单账号
            public_front.test_close_trader(var_manager)
            # 平仓跟单账号
            public_front.test_close_follow(var_manager)
            # 清理魔术号相关数据
            public_front.test_query_magic(var_manager, logged_session)
            # 清理账号ID相关数据
            public_front.test_query_follow_passid(var_manager, logged_session)
            # 登录MT4账号获取token
            public_front.test_mt4_login(var_manager)
            # MT4平台开仓操作
            public_front.test_mt4_open(var_manager)

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @pytest.mark.retry(n=3, delay=5)
        @allure.title("账号管理-持仓订单-喊单者账号ID查询-开仓后")
        def test_query_opentrader_passid(self, var_manager, logged_session):
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
                    '/online/cgform/api/getData/402883977b38c9ca017b38c9caff0000',
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
                    attach_body = f"账号ID查询[{trader_account}]，返回的trader_id列表为空（暂无数据）"
                else:
                    attach_body = f"账号ID查询[{trader_account}]，返回 {len(trader_id_list)} 条记录"

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
                            message=f"订单号数据正确",
                            attachment_name="订单号详情"
                        )
                        logger.info(f"订单号数据正确,开仓订单号：{ticket_open} 喊单者订单号：{order_no}")

                    with allure.step("喊单手数校验-MT4开仓手数和持仓订单手数"):
                        order_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                        logging.info(f"喊单者手数是: {order_size}")

                        lots_open = var_manager.get_variable("lots_open")

                        self.verify_data(
                            actual_value=float(order_size),
                            expected_value=float(lots_open),
                            op=CompareOp.EQ,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"喊单者手数：{order_size} MT4开仓手数：{lots_open}")

                    with allure.step("喊单的订单方向校验"):
                        type = self.json_utils.extract(response.json(), "$.result.records[0].type")
                        logging.info(f"喊单者方向是: {type}")

                        self.verify_data(
                            actual_value=float(type),
                            expected_value=float(0),
                            op=CompareOp.EQ,
                            message=f"喊单者方向符合预期",
                            attachment_name="喊单者方向详情"
                        )
                        logger.info(f"喊单者方向：{type}")
                        allure.attach("0:buy  1:sell", "方向解释", allure.attachment_type.TEXT)

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库提取数据-提取跟单订单号")
        def test_dbquery_openorder(self, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否新增成功"):
                ticket_open = var_manager.get_variable("ticket_open")

                # 优化后的数据库查询
                db_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM bchain_trader_subscribe_order WHERE master_ticket = %s",
                    (ticket_open,),
                )

                # 提取数据库中的值
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

            with allure.step("2. 提取数据库中的值"):
                slave_ticket = db_data[0]["slave_ticket"]
                print(f"输出：{slave_ticket}")
                logging.info(f"跟单账号订单号: {slave_ticket}")
                var_manager.set_runtime_variable("slave_ticket", slave_ticket)

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("账号管理-持仓订单-跟单账号ID查询-开仓后")
        def test_query_openfollow_passid(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_pass_id = var_manager.get_variable("follow_pass_id")
                follow_account = var_manager.get_variable("follow_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "trader_id": follow_pass_id,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 20,
                    "superQueryMatchType": "and"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/402883977b38c9ca017b38c9caff0000',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 提取数据"):
                order_no = self.json_utils.extract(response.json(), "$.result.records[0].order_no")
                var_manager.set_runtime_variable("order_no", order_no)
                allure.attach(f"{order_no}", "跟单订单号", allure.attachment_type.TEXT)

            with allure.step(f"3. 查询校验"):
                trader_id_list = self.json_utils.extract(
                    response.json(),
                    "$.result.records[0].trader_id",
                    default=[],
                    multi_match=True
                )

                if not trader_id_list:
                    attach_body = f"账号ID查询[{follow_account}]，返回的trader_id列表为空（暂无数据）"
                else:
                    attach_body = f"账号ID查询[{follow_account}]，返回 {len(trader_id_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"账号ID:{follow_account}查询结果",
                    attachment_type="text/plain"
                )

                for idx, trader_id in enumerate(trader_id_list):
                    self.verify_data(
                        actual_value=int(trader_id),
                        expected_value=int(follow_pass_id),
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的账号ID应为{trader_id}",
                        attachment_name=f"账号ID:{follow_pass_id}第 {idx + 1} 条记录校验"
                    )

                with allure.step("喊单者订单号校验"):
                    master_order_no = self.json_utils.extract(response.json(), "$.result.records[0].master_order_no")
                    ticket_open = var_manager.get_variable("ticket_open")

                    self.verify_data(
                        actual_value=ticket_open,
                        expected_value=master_order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"订单号数据正确",
                        attachment_name="订单号详情"
                    )
                    logger.info(f"订单号数据正确,开仓订单号：{ticket_open} 喊单者订单号：{master_order_no}")

                with allure.step("跟单订单号校验"):
                    slave_ticket = var_manager.get_variable("slave_ticket")
                    self.verify_data(
                        actual_value=slave_ticket,
                        expected_value=order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"订单号数据正确",
                        attachment_name="订单号详情"
                    )
                    logger.info(f"订单号数据正确,跟单者订单号：{order_no} 数据库数据：{slave_ticket}")

                with allure.step("跟单手数校验"):
                    add_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                    if not add_size:
                        allure.attach("订单手数数据为空", "订单手数数据", allure.attachment_type.TEXT)
                    else:
                        lots_open = var_manager.get_variable("lots_open")
                        follow_periodP = var_manager.get_variable("follow_periodP")
                        trader_periodP = var_manager.get_variable("trader_periodP")
                        # 获取跟单净值比例
                        fixed_proportion = var_manager.get_variable("fixed_proportion")
                        # 百分比数据转换
                        follow_fixed_decimal = percentage_to_decimal(fixed_proportion)
                        expected_lots_open = lots_open * (follow_periodP / trader_periodP) * follow_fixed_decimal
                        # 四舍五入保留两位小数
                        expected_lots_open = round(expected_lots_open, 2)

                        # 最小手数限制（0.01）
                        min_order_size = 0.01
                        if expected_lots_open < min_order_size:
                            allure.attach(
                                f"计算预期手数{expected_lots_open} < 最小手数{min_order_size}，强制重置为{min_order_size}",
                                "预期手数调整说明", allure.attachment_type.TEXT)
                            expected_lots_open = min_order_size

                        self.verify_data(
                            actual_value=float(add_size),
                            expected_value=float(expected_lots_open),
                            op=CompareOp.EQ,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"跟单者手数：{add_size}")

                with allure.step("跟单的订单方向校验"):
                    type = self.json_utils.extract(response.json(), "$.result.records[0].type")
                    logging.info(f"跟单方向是: {type}")

                    self.verify_data(
                        actual_value=float(type),
                        expected_value=float(0),
                        op=CompareOp.EQ,
                        message=f"跟单方向符合预期",
                        attachment_name="跟单方向详情"
                    )
                    logger.info(f"跟单方向：{type}")
                    allure.attach("0:buy  1:sell", "方向解释", allure.attachment_type.TEXT)

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-开仓日志-喊单账户查询-开仓后")
        def test_query_opentrader_getdata(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_account = var_manager.get_variable("trader_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "master_account": trader_account,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 20,
                    "superQueryMatchType": "and"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/2c934301834efb6801834efbe1ba0002',
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
                master_ticket_list = self.json_utils.extract(
                    response.json(),
                    "$.result.records[0].master_ticket",
                    default=[],
                    multi_match=True
                )

                if not master_ticket_list:
                    attach_body = f"喊单账户查询[{trader_account}]，返回的master_ticket列表为空（暂无数据）"
                else:
                    attach_body = f"喊单账户查询[{trader_account}]，返回 {len(master_ticket_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"喊单账户:{trader_account}查询结果",
                    attachment_type="text/plain"
                )

                for idx, master_ticket in enumerate(master_ticket_list):
                    ticket_open = var_manager.get_variable("ticket_open")
                    self.verify_data(
                        actual_value=master_ticket,
                        expected_value=ticket_open,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的订单号应为{master_ticket}",
                        attachment_name=f"喊单账户:{trader_account}第 {idx + 1} 条记录校验"
                    )

                with allure.step("喊单者手数校验"):
                    master_lots = self.json_utils.extract(response.json(),
                                                          "$.result.records[0].master_lots")
                    lots_open = var_manager.get_variable("lots_open")

                    self.verify_data(
                        actual_value=float(master_lots),
                        expected_value=float(lots_open),
                        op=CompareOp.EQ,
                        message=f"喊单者手数符合预期",
                        attachment_name="喊单者手数详情"
                    )
                    logger.info(f"喊单者手数验证通过: {lots_open}")

                with allure.step("交易币种校验"):
                    master_symbol = self.json_utils.extract(response.json(),
                                                            "$.result.records[0].master_symbol")
                    symbol = var_manager.get_variable("symbol")

                    self.verify_data(
                        actual_value=master_symbol,
                        expected_value=symbol,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"交易币种符合预期",
                        attachment_name="交易币种详情"
                    )
                    logger.info(f"交易币种验证通过: {master_symbol}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-开仓日志-开平仓明细-开仓后")
        def test_query_opentrader_detail(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                ticket_open = var_manager.get_variable("ticket_open")
                params = {
                    "_t": current_timestamp_seconds,
                    "pageNo": 1,
                    "pageSize": 20,
                    "self_master_ticket": ticket_open
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgreport/api/getColumnsAndData/1568899025974796289',
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
                slave_ticket_list = self.json_utils.extract(
                    response.json(),
                    "$.result.data.records[0].slave_ticket",
                    default=[],
                    multi_match=True
                )
                follow_account = var_manager.get_variable("follow_account")
                if not slave_ticket_list:
                    attach_body = f"跟单账号：{follow_account}，返回的slave_ticket列表为空（暂无数据）"
                else:
                    attach_body = f"跟单账号：{follow_account}，返回 {len(slave_ticket_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"跟单账号：{follow_account}结果",
                    attachment_type="text/plain"
                )

                for idx, slave_ticket in enumerate(slave_ticket_list):
                    order_no = var_manager.get_variable("order_no")
                    self.verify_data(
                        actual_value=slave_ticket,
                        expected_value=order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的订单号应为{slave_ticket}",
                        attachment_name=f"跟单账户:{follow_account}第 {idx + 1} 条记录校验"
                    )

                with allure.step("喊单者订单号校验"):
                    master_ticket = self.json_utils.extract(response.json(),
                                                            "$.result.data.records[0].master_ticket")
                    ticket_open = var_manager.get_variable("ticket_open")

                    self.verify_data(
                        actual_value=master_ticket,
                        expected_value=ticket_open,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"喊单者订单号符合预期",
                        attachment_name="喊单者订单号详情"
                    )
                    logger.info(f"喊单者订单号验证通过: {master_ticket}")

                with allure.step("喊单者手数校验"):
                    master_lots = self.json_utils.extract(response.json(),
                                                          "$.result.data.records[0].master_lots")
                    lots_open = var_manager.get_variable("lots_open")

                    self.verify_data(
                        actual_value=float(master_lots),
                        expected_value=float(lots_open),
                        op=CompareOp.EQ,
                        message=f"喊单者手数符合预期",
                        attachment_name="喊单者手数详情"
                    )
                    logger.info(f"喊单者手数验证通过: {master_lots}")

                with allure.step("跟单手数校验"):
                    slave_lots = self.json_utils.extract(response.json(),
                                                         "$.result.data.records[0].slave_lots")
                    if not slave_lots:
                        allure.attach("跟单手数返回为空", "跟单手数详情", allure.attachment_type.TEXT)
                    else:
                        lots_open = var_manager.get_variable("lots_open")
                        follow_periodP = var_manager.get_variable("follow_periodP")
                        trader_periodP = var_manager.get_variable("trader_periodP")
                        # 获取跟单净值比例
                        fixed_proportion = var_manager.get_variable("fixed_proportion")
                        # 百分比数据转换
                        follow_fixed_decimal = percentage_to_decimal(fixed_proportion)
                        expected_lots_open = lots_open * (follow_periodP / trader_periodP) * follow_fixed_decimal
                        # 四舍五入保留两位小数
                        expected_lots_open = round(expected_lots_open, 2)

                        # 最小手数限制（0.01）
                        min_order_size = 0.01
                        if expected_lots_open < min_order_size:
                            allure.attach(
                                f"计算预期手数{expected_lots_open} < 最小手数{min_order_size}，强制重置为{min_order_size}",
                                "预期手数调整说明", allure.attachment_type.TEXT)
                            expected_lots_open = min_order_size

                        self.verify_data(
                            actual_value=float(slave_lots),
                            expected_value=float(expected_lots_open),
                            op=CompareOp.EQ,
                            message=f"跟单手数符合预期",
                            attachment_name="跟单手数详情"
                        )
                        logger.info(f"跟单手数验证通过: {slave_lots}")

                with allure.step("交易币种校验"):
                    master_symbol = self.json_utils.extract(response.json(),
                                                            "$.result.data.records[0].master_symbol")
                    symbol = var_manager.get_variable("symbol")

                    self.verify_data(
                        actual_value=master_symbol,
                        expected_value=symbol,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"交易币种符合预期",
                        attachment_name="交易币种详情"
                    )
                    logger.info(f"交易币种验证通过: {master_symbol}")

                # @pytest.mark.skipif(True, reason="跳过此用例")

        @pytest.mark.retry(n=3, delay=10)
        @allure.title("跟单管理-VPS管理-喊单者账号-开仓后")
        def test_query_opentrader_getRecordList(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_account = var_manager.get_variable("trader_account")
                vpsrunIpAddr = var_manager.get_variable("vpsrunIpAddr")
                params = {
                    "_t": current_timestamp_seconds,
                    "pageNo": "1",
                    "pageSize": "50",
                    "accountLike": trader_account,
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
                with allure.step("喊单者手数校验-MT4开仓手数和持仓订单手数"):
                    totalLots = self.json_utils.extract(response.json(), "$.records[0].totalLots")
                    logging.info(f"手数是: {totalLots}")

                    lots_open = var_manager.get_variable("lots_open")

                    self.verify_data(
                        actual_value=float(totalLots),
                        expected_value=float(lots_open),
                        op=CompareOp.EQ,
                        message=f"手数符合预期",
                        attachment_name="手数详情"
                    )
                    logger.info(f"喊单者手数：{totalLots} MT4开仓手数：{lots_open}")

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
                    if not totalLots:
                        allure.attach("跟单手数为空", "跟单手数详情", allure.attachment_type.TEXT)
                    else:
                        lots_open = var_manager.get_variable("lots_open")
                        follow_periodP = var_manager.get_variable("follow_periodP")
                        trader_periodP = var_manager.get_variable("trader_periodP")
                        # 获取跟单净值比例
                        fixed_proportion = var_manager.get_variable("fixed_proportion")
                        # 百分比数据转换
                        follow_fixed_decimal = percentage_to_decimal(fixed_proportion)
                        expected_lots_open = lots_open * (follow_periodP / trader_periodP) * follow_fixed_decimal
                        # 四舍五入保留两位小数
                        expected_lots_open = round(expected_lots_open, 2)

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
                        logger.info(f"跟单者手数：{totalLots}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("MT4平台平仓操作")
        def test_mt4_close(self, var_manager, db_transaction):
            # 实例化类
            public_front = PublicUtils()

            # MT4平台平仓操作
            public_front.test_mt4_close(var_manager, db_transaction)

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-开仓日志-开平仓明细-平仓后")
        def test_query_closetrader_detail(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                ticket_open = var_manager.get_variable("ticket_open")
                params = {
                    "_t": current_timestamp_seconds,
                    "pageNo": 1,
                    "pageSize": 20,
                    "self_master_ticket": ticket_open
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgreport/api/getColumnsAndData/1568899025974796289',
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
                slave_ticket_list = self.json_utils.extract(
                    response.json(),
                    "$.result.data.records[0].slave_ticket",
                    default=[],
                    multi_match=True
                )
                follow_account = var_manager.get_variable("follow_account")
                if not slave_ticket_list:
                    attach_body = f"跟单账号：{follow_account}，返回的slave_ticket列表为空（暂无数据）"
                else:
                    attach_body = f"跟单账号：{follow_account}，返回 {len(slave_ticket_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"跟单账号：{follow_account}结果",
                    attachment_type="text/plain"
                )

                for idx, slave_ticket in enumerate(slave_ticket_list):
                    order_no = var_manager.get_variable("order_no")
                    self.verify_data(
                        actual_value=slave_ticket,
                        expected_value=order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的订单号应为{slave_ticket}",
                        attachment_name=f"跟单账户:{follow_account}第 {idx + 1} 条记录校验"
                    )

                with allure.step("喊单者订单号校验"):
                    master_ticket = self.json_utils.extract(response.json(),
                                                            "$.result.data.records[0].master_ticket")
                    ticket_open = var_manager.get_variable("ticket_open")

                    self.verify_data(
                        actual_value=master_ticket,
                        expected_value=ticket_open,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"喊单者订单号符合预期",
                        attachment_name="喊单者订单号详情"
                    )
                    logger.info(f"喊单者订单号验证通过: {master_ticket}")

                with allure.step("喊单者手数校验"):
                    master_lots = self.json_utils.extract(response.json(),
                                                          "$.result.data.records[0].master_lots")
                    lots_open = var_manager.get_variable("lots_open")

                    self.verify_data(
                        actual_value=float(master_lots),
                        expected_value=float(lots_open),
                        op=CompareOp.EQ,
                        message=f"喊单者手数符合预期",
                        attachment_name="喊单者手数详情"
                    )
                    logger.info(f"喊单者手数验证通过: {master_lots}")

                with allure.step("跟单手数校验"):
                    slave_lots = self.json_utils.extract(response.json(),
                                                         "$.result.data.records[0].slave_lots")
                    if not slave_lots:
                        allure.attach("跟单手数为空", "跟单手数详情", allure.attachment_type.TEXT)
                    else:
                        lots_open = var_manager.get_variable("lots_open")
                        follow_periodP = var_manager.get_variable("follow_periodP")
                        trader_periodP = var_manager.get_variable("trader_periodP")
                        # 获取跟单净值比例
                        fixed_proportion = var_manager.get_variable("fixed_proportion")
                        # 百分比数据转换
                        follow_fixed_decimal = percentage_to_decimal(fixed_proportion)
                        expected_lots_open = lots_open * (follow_periodP / trader_periodP) * follow_fixed_decimal
                        # 四舍五入保留两位小数
                        expected_lots_open = round(expected_lots_open, 2)

                        # 最小手数限制（0.01）
                        min_order_size = 0.01
                        if expected_lots_open < min_order_size:
                            allure.attach(
                                f"计算预期手数{expected_lots_open} < 最小手数{min_order_size}，强制重置为{min_order_size}",
                                "预期手数调整说明", allure.attachment_type.TEXT)
                            expected_lots_open = min_order_size

                        self.verify_data(
                            actual_value=float(slave_lots),
                            expected_value=float(expected_lots_open),
                            op=CompareOp.EQ,
                            message=f"跟单手数符合预期",
                            attachment_name="跟单手数详情"
                        )
                        logger.info(f"跟单手数验证通过: {slave_lots}")

                with allure.step("交易币种校验"):
                    master_symbol = self.json_utils.extract(response.json(),
                                                            "$.result.data.records[0].master_symbol")
                    symbol = var_manager.get_variable("symbol")

                    self.verify_data(
                        actual_value=master_symbol,
                        expected_value=symbol,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"交易币种符合预期",
                        attachment_name="交易币种详情"
                    )
                    logger.info(f"交易币种验证通过: {master_symbol}")

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
                            message=f"订单号数据正确",
                            attachment_name="订单号详情"
                        )
                        logger.info(f"订单号数据正确,开仓订单号：{ticket_open} 喊单者订单号：{order_no}")

                    with allure.step("喊单手数校验-MT4开仓手数和持仓订单手数"):
                        order_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                        logging.info(f"喊单者手数是: {order_size}")

                        lots_open = var_manager.get_variable("lots_open")
                        self.verify_data(
                            actual_value=float(order_size),
                            expected_value=float(lots_open),
                            op=CompareOp.EQ,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"喊单者手数：{order_size} MT4开仓手数：{lots_open}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("账号管理-历史订单-跟单MT4账户查询-平仓后")
        def test_query_follow_id(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_pass_id = var_manager.get_variable("follow_pass_id")
                follow_account = var_manager.get_variable("follow_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "trader_id": follow_pass_id,
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

            with allure.step("3. 提取数据"):
                order_no = self.json_utils.extract(response.json(), "$.result.records[0].order_no")
                var_manager.set_runtime_variable("order_no", order_no)
                allure.attach(f"{order_no}", "跟单订单号", allure.attachment_type.TEXT)

            with allure.step(f"3. 查询校验"):
                trader_id_list = self.json_utils.extract(
                    response.json(),
                    "$.result.records[0].trader_id",
                    default=[],
                    multi_match=True
                )

                if not trader_id_list:
                    attach_body = f"MT4账号查询[{follow_account}]，返回的trader_id列表为空（暂无数据）"
                else:
                    attach_body = f"MT4账号查询[{follow_account}]，返回 {len(trader_id_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"账号ID:{follow_account}查询结果",
                    attachment_type="text/plain"
                )

                for idx, trader_id in enumerate(trader_id_list):
                    self.verify_data(
                        actual_value=int(trader_id),
                        expected_value=int(follow_pass_id),
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的账号ID应为{trader_id}",
                        attachment_name=f"账号ID:{follow_pass_id}第 {idx + 1} 条记录校验"
                    )

                with allure.step("喊单者订单号校验"):
                    master_order_no = self.json_utils.extract(response.json(),
                                                              "$.result.records[0].master_order_no")
                    ticket_open = var_manager.get_variable("ticket_open")

                    self.verify_data(
                        actual_value=ticket_open,
                        expected_value=master_order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"订单号数据正确",
                        attachment_name="订单号详情"
                    )
                    logger.info(f"订单号数据正确,开仓订单号：{ticket_open} 喊单者订单号：{master_order_no}")

                with allure.step("跟单订单号校验"):
                    slave_ticket = var_manager.get_variable("slave_ticket")
                    self.verify_data(
                        actual_value=slave_ticket,
                        expected_value=order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"订单号数据正确",
                        attachment_name="订单号详情"
                    )
                    logger.info(f"订单号数据正确,跟单者订单号：{order_no} 数据库数据：{slave_ticket}")

                with allure.step("跟单手数校验"):
                    add_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                    if not add_size:
                        allure.attach("订单手数数据为空", "订单手数数据", allure.attachment_type.TEXT)
                    else:
                        lots_open = var_manager.get_variable("lots_open")
                        follow_periodP = var_manager.get_variable("follow_periodP")
                        trader_periodP = var_manager.get_variable("trader_periodP")
                        # 获取跟单净值比例
                        fixed_proportion = var_manager.get_variable("fixed_proportion")
                        # 百分比数据转换
                        follow_fixed_decimal = percentage_to_decimal(fixed_proportion)
                        expected_lots_open = lots_open * (follow_periodP / trader_periodP) * follow_fixed_decimal
                        # 四舍五入保留两位小数
                        expected_lots_open = round(expected_lots_open, 2)

                        # 最小手数限制（0.01）
                        min_order_size = 0.01
                        if expected_lots_open < min_order_size:
                            allure.attach(
                                f"计算预期手数{expected_lots_open} < 最小手数{min_order_size}，强制重置为{min_order_size}",
                                "预期手数调整说明", allure.attachment_type.TEXT)
                            expected_lots_open = min_order_size

                        self.verify_data(
                            actual_value=float(add_size),
                            expected_value=float(expected_lots_open),
                            op=CompareOp.EQ,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"跟单者手数：{add_size}")

        @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("账号管理-持仓订单-喊单者账号ID查询-平仓后")
        def test_query_closetrader_passid(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_pass_id = var_manager.get_variable("trader_pass_id")
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
                    '/online/cgform/api/getData/402883977b38c9ca017b38c9caff0000',
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
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.result.records"
                )
                logging.info("查询结果符合预期：records为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("账号管理-持仓订单-跟单账号ID查询-平仓后")
        def test_query_closefollow_passid(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_pass_id = var_manager.get_variable("follow_pass_id")
                params = {
                    "_t": current_timestamp_seconds,
                    "trader_id": follow_pass_id,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 20,
                    "superQueryMatchType": "and"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/402883977b38c9ca017b38c9caff0000',
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
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.result.records"
                )
                logging.info("查询结果符合预期：records为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        @pytest.mark.skipif(True, reason="跳过此用例")
        @pytest.mark.retry(n=3, delay=5)
        @allure.title("跟单管理-VPS管理-喊单者账号-平仓后")
        def test_query_closetrader_getRecordList(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_account = var_manager.get_variable("trader_account")
                vpsrunIpAddr = var_manager.get_variable("vpsrunIpAddr")
                params = {
                    "_t": current_timestamp_seconds,
                    "pageNo": "1",
                    "pageSize": "50",
                    "accountLike": trader_account,
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
                with allure.step("喊单者手数校验-MT4开仓手数和持仓订单手数"):
                    totalLots = self.json_utils.extract(response.json(), "$.records[0].totalLots")
                    logging.info(f"手数是: {totalLots}")

                    self.verify_data(
                        actual_value=float(totalLots),
                        expected_value=float(0),
                        op=CompareOp.EQ,
                        message=f"手数符合预期",
                        attachment_name="手数详情"
                    )
                    logger.info(f"平仓后手数应为：0，实际是：{totalLots}")

        @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-VPS管理-跟单者账号-平仓后")
        def test_query_closefollow_getRecordList(self, var_manager, logged_session):
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

                    self.verify_data(
                        actual_value=float(totalLots),
                        expected_value=float(0),
                        op=CompareOp.EQ,
                        message=f"手数符合预期",
                        attachment_name="手数详情"
                    )
                    logger.info(f"平仓后手数应为：0，实际是：{totalLots}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库提取数据-平仓时间差")
        def test_dbquery_closeorder(self, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否新增成功"):
                ticket_open = var_manager.get_variable("ticket_open")

                # 优化后的数据库查询
                db_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM bchain_trader_subscribe_order WHERE master_ticket = %s",
                    (ticket_open,),
                )

                # 提取数据库中的值
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

            with allure.step("2. 提取数据库中的值"):
                slave_ticket = db_data[0]["slave_ticket"]
                print(f"输出：{slave_ticket}")
                logging.info(f"跟单账号订单号: {slave_ticket}")
                var_manager.set_runtime_variable("slave_ticket", slave_ticket)

                close_time_difference = db_data[0]["close_time_difference"]
                print(f"输出：{close_time_difference}")
                logging.info(f"平仓时间差（毫秒）: {close_time_difference}")
                var_manager.set_runtime_variable("close_time_difference", close_time_difference)
                allure.attach(f"平仓时间差（毫秒）: {close_time_difference}", "平仓时间差")

    @allure.story("场景2：跟随方式-按净值-50%")
    @allure.description("""
    ### 测试说明
    - 前置条件：有喊单账号、跟单账号，跟单已经和喊单有订阅关系
      1. 修改订阅信息，跟随方式-按净值-50%
      2. MT4进行登录，然后进行开仓，总手数0.01
      3. 账号管理-持仓订单-喊单和跟单数据校验
      4. 跟单管理-开仓日志-喊单和跟单数据校验
      5. 跟单管理-VPS管理-喊单和跟单数据校验
      6. MT4进行平仓
      7. 账号管理-历史订单-喊单和跟单数据校验
      8. 跟单管理-开仓日志-喊单和跟单数据校验
    - 预期结果：喊单和跟单数据校验正确
    """)
    # @pytest.mark.skipif(True, reason="跳过此用例")
    class Test_orderseng2(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-实时跟单-修改订阅数据")
        def test_query_updata_editPa(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_jeecg_rowkey = var_manager.get_variable("follow_jeecg_rowkey")
                data = {
                    "id": follow_jeecg_rowkey,
                    "direction": "FORWARD",
                    "followingMode": 4,
                    "fixedProportion": 50,
                    "fixedLots": None
                }
                response = self.send_put_request(
                    logged_session,
                    '/blockchain/master-slave/editPa',
                    json_data=data
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-实时跟单-订阅列表数据")
        def test_query_getColumnsAndData(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_account = var_manager.get_variable("follow_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "account": follow_account,
                    "pageNo": "1",
                    "pageSize": "20",
                    "status": "NORMAL,AUDIT"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )
            with allure.step("3. 提取数据"):
                fixed_proportion = self.json_utils.extract(response.json(),
                                                           "$.result.data.records[0].fixed_proportion")
                var_manager.set_runtime_variable("fixed_proportion", fixed_proportion)

        @pytest.mark.retry(n=3, delay=10)
        @allure.title("跟单管理-VPS管理-提取喊单者净值")
        def test_query_get_traderquit(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_account = var_manager.get_variable("trader_account")
                vpsrunIpAddr = var_manager.get_variable("vpsrunIpAddr")
                params = {
                    "_t": current_timestamp_seconds,
                    "pageNo": "1",
                    "pageSize": "50",
                    "accountLike": trader_account,
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

            with allure.step(f"3. 提取净值数据"):
                trader_equity = self.json_utils.extract(response.json(), "$.records[0].equity")
                currency = self.json_utils.extract(response.json(), "$.records[0].currency")

                if currency == "USD":
                    trader_periodP = round(float(trader_equity) * 1.0, 2)
                elif currency == "JPY":
                    trader_periodP = round(float(trader_equity) * 0.00672, 2)
                elif currency == "AUD":
                    trader_periodP = round(float(trader_equity) * 0.6251, 2)
                elif currency == "USC":
                    trader_periodP = round(float(trader_equity) * 0.01, 2)
                else:
                    pytest.fail(f"不支持的币种：{currency}，请补充币种转换逻辑")

                logging.info(f"币种的转换详情,当前币种{currency}，转换前：{trader_equity},转换后：{trader_periodP}")
                allure.attach(f"当前币种{currency}，转换前：{trader_equity},转换后：{trader_periodP}",
                              "币种类型转换详情", allure.attachment_type.TEXT)
                var_manager.set_runtime_variable("trader_periodP", trader_periodP)

        @allure.title("跟单管理-VPS管理-提取跟单者净值")
        def test_query_get_followquit(self, var_manager, logged_session):
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

            with allure.step(f"3. 提取净值数据"):
                follow_equity = self.json_utils.extract(response.json(), "$.records[0].equity")
                currency = self.json_utils.extract(response.json(), "$.records[0].currency")

                if currency == "USD":
                    follow_periodP = round(float(follow_equity) * 1.0, 2)
                elif currency == "JPY":
                    follow_periodP = round(float(follow_equity) * 0.00672, 2)
                elif currency == "AUD":
                    follow_periodP = round(float(follow_equity) * 0.6251, 2)
                elif currency == "USC":
                    follow_periodP = round(float(follow_equity) * 0.01, 2)
                else:
                    pytest.fail(f"不支持的币种：{currency}，请补充币种转换逻辑")

                logging.info(f"币种的转换详情,当前币种{currency}，转换前：{follow_equity},转换后：{follow_periodP}")
                allure.attach(f"当前币种{currency}，转换前：{follow_equity},转换后：{follow_periodP}",
                              "币种类型转换详情", allure.attachment_type.TEXT)
                var_manager.set_runtime_variable("follow_periodP", follow_periodP)

        @allure.title("公共方法-校验前操作")
        def test_run_public(self, var_manager, logged_session):
            # 实例化类
            public_front = PublicUtils()

            # 按顺序调用
            # 登录获取 token
            public_front.test_login(var_manager)
            # 平仓喊单账号
            public_front.test_close_trader(var_manager)
            # 平仓跟单账号
            public_front.test_close_follow(var_manager)
            # 清理魔术号相关数据
            public_front.test_query_magic(var_manager, logged_session)
            # 清理账号ID相关数据
            public_front.test_query_follow_passid(var_manager, logged_session)
            # 登录MT4账号获取token
            public_front.test_mt4_login(var_manager)
            # MT4平台开仓操作
            public_front.test_mt4_open(var_manager)

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @pytest.mark.retry(n=3, delay=5)
        @allure.title("账号管理-持仓订单-喊单者账号ID查询-开仓后")
        def test_query_opentrader_passid(self, var_manager, logged_session):
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
                    '/online/cgform/api/getData/402883977b38c9ca017b38c9caff0000',
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
                    attach_body = f"账号ID查询[{trader_account}]，返回的trader_id列表为空（暂无数据）"
                else:
                    attach_body = f"账号ID查询[{trader_account}]，返回 {len(trader_id_list)} 条记录"

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
                            message=f"订单号数据正确",
                            attachment_name="订单号详情"
                        )
                        logger.info(f"订单号数据正确,开仓订单号：{ticket_open} 喊单者订单号：{order_no}")

                    with allure.step("喊单手数校验-MT4开仓手数和持仓订单手数"):
                        order_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                        logging.info(f"喊单者手数是: {order_size}")

                        lots_open = var_manager.get_variable("lots_open")

                        self.verify_data(
                            actual_value=float(order_size),
                            expected_value=float(lots_open),
                            op=CompareOp.EQ,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"喊单者手数：{order_size} MT4开仓手数：{lots_open}")

                    with allure.step("喊单的订单方向校验"):
                        type = self.json_utils.extract(response.json(), "$.result.records[0].type")
                        logging.info(f"喊单者方向是: {type}")

                        self.verify_data(
                            actual_value=float(type),
                            expected_value=float(0),
                            op=CompareOp.EQ,
                            message=f"喊单者方向符合预期",
                            attachment_name="喊单者方向详情"
                        )
                        logger.info(f"喊单者方向：{type}")
                        allure.attach("0:buy  1:sell", "方向解释", allure.attachment_type.TEXT)

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库提取数据-提取跟单订单号")
        def test_dbquery_openorder(self, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否新增成功"):
                ticket_open = var_manager.get_variable("ticket_open")

                # 优化后的数据库查询
                db_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM bchain_trader_subscribe_order WHERE master_ticket = %s",
                    (ticket_open,),
                )

                # 提取数据库中的值
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

            with allure.step("2. 提取数据库中的值"):
                slave_ticket = db_data[0]["slave_ticket"]
                print(f"输出：{slave_ticket}")
                logging.info(f"跟单账号订单号: {slave_ticket}")
                var_manager.set_runtime_variable("slave_ticket", slave_ticket)

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("账号管理-持仓订单-跟单账号ID查询-开仓后")
        def test_query_openfollow_passid(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_pass_id = var_manager.get_variable("follow_pass_id")
                follow_account = var_manager.get_variable("follow_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "trader_id": follow_pass_id,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 20,
                    "superQueryMatchType": "and"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/402883977b38c9ca017b38c9caff0000',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 提取数据"):
                order_no = self.json_utils.extract(response.json(), "$.result.records[0].order_no")
                var_manager.set_runtime_variable("order_no", order_no)
                allure.attach(f"{order_no}", "跟单订单号", allure.attachment_type.TEXT)

            with allure.step(f"3. 查询校验"):
                trader_id_list = self.json_utils.extract(
                    response.json(),
                    "$.result.records[0].trader_id",
                    default=[],
                    multi_match=True
                )

                if not trader_id_list:
                    attach_body = f"账号ID查询[{follow_account}]，返回的trader_id列表为空（暂无数据）"
                else:
                    attach_body = f"账号ID查询[{follow_account}]，返回 {len(trader_id_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"账号ID:{follow_account}查询结果",
                    attachment_type="text/plain"
                )

                for idx, trader_id in enumerate(trader_id_list):
                    self.verify_data(
                        actual_value=int(trader_id),
                        expected_value=int(follow_pass_id),
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的账号ID应为{trader_id}",
                        attachment_name=f"账号ID:{follow_pass_id}第 {idx + 1} 条记录校验"
                    )

                with allure.step("喊单者订单号校验"):
                    master_order_no = self.json_utils.extract(response.json(), "$.result.records[0].master_order_no")
                    ticket_open = var_manager.get_variable("ticket_open")

                    self.verify_data(
                        actual_value=ticket_open,
                        expected_value=master_order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"订单号数据正确",
                        attachment_name="订单号详情"
                    )
                    logger.info(f"订单号数据正确,开仓订单号：{ticket_open} 喊单者订单号：{master_order_no}")

                with allure.step("跟单订单号校验"):
                    slave_ticket = var_manager.get_variable("slave_ticket")
                    self.verify_data(
                        actual_value=slave_ticket,
                        expected_value=order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"订单号数据正确",
                        attachment_name="订单号详情"
                    )
                    logger.info(f"订单号数据正确,跟单者订单号：{order_no} 数据库数据：{slave_ticket}")

                with allure.step("跟单手数校验"):
                    add_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                    if not add_size:
                        allure.attach("订单手数数据为空", "订单手数数据", allure.attachment_type.TEXT)
                    else:
                        lots_open = var_manager.get_variable("lots_open")
                        follow_periodP = var_manager.get_variable("follow_periodP")
                        trader_periodP = var_manager.get_variable("trader_periodP")
                        # 获取跟单净值比例
                        fixed_proportion = var_manager.get_variable("fixed_proportion")
                        # 百分比数据转换
                        follow_fixed_decimal = percentage_to_decimal(fixed_proportion)
                        expected_lots_open = lots_open * (follow_periodP / trader_periodP) * follow_fixed_decimal
                        # 四舍五入保留两位小数
                        expected_lots_open = round(expected_lots_open, 2)

                        # 最小手数限制（0.01）
                        min_order_size = 0.01
                        if expected_lots_open < min_order_size:
                            allure.attach(
                                f"计算预期手数{expected_lots_open} < 最小手数{min_order_size}，强制重置为{min_order_size}",
                                "预期手数调整说明", allure.attachment_type.TEXT)
                            expected_lots_open = min_order_size

                        self.verify_data(
                            actual_value=float(add_size),
                            expected_value=float(expected_lots_open),
                            op=CompareOp.EQ,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"跟单者手数：{add_size}")

                with allure.step("跟单的订单方向校验"):
                    type = self.json_utils.extract(response.json(), "$.result.records[0].type")
                    logging.info(f"跟单方向是: {type}")

                    self.verify_data(
                        actual_value=float(type),
                        expected_value=float(0),
                        op=CompareOp.EQ,
                        message=f"跟单方向符合预期",
                        attachment_name="跟单方向详情"
                    )
                    logger.info(f"跟单方向：{type}")
                    allure.attach("0:buy  1:sell", "方向解释", allure.attachment_type.TEXT)

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-开仓日志-喊单账户查询-开仓后")
        def test_query_opentrader_getdata(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_account = var_manager.get_variable("trader_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "master_account": trader_account,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 20,
                    "superQueryMatchType": "and"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/2c934301834efb6801834efbe1ba0002',
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
                master_ticket_list = self.json_utils.extract(
                    response.json(),
                    "$.result.records[0].master_ticket",
                    default=[],
                    multi_match=True
                )

                if not master_ticket_list:
                    attach_body = f"喊单账户查询[{trader_account}]，返回的master_ticket列表为空（暂无数据）"
                else:
                    attach_body = f"喊单账户查询[{trader_account}]，返回 {len(master_ticket_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"喊单账户:{trader_account}查询结果",
                    attachment_type="text/plain"
                )

                for idx, master_ticket in enumerate(master_ticket_list):
                    ticket_open = var_manager.get_variable("ticket_open")
                    self.verify_data(
                        actual_value=master_ticket,
                        expected_value=ticket_open,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的订单号应为{master_ticket}",
                        attachment_name=f"喊单账户:{trader_account}第 {idx + 1} 条记录校验"
                    )

                with allure.step("喊单者手数校验"):
                    master_lots = self.json_utils.extract(response.json(),
                                                          "$.result.records[0].master_lots")
                    lots_open = var_manager.get_variable("lots_open")

                    self.verify_data(
                        actual_value=float(master_lots),
                        expected_value=float(lots_open),
                        op=CompareOp.EQ,
                        message=f"喊单者手数符合预期",
                        attachment_name="喊单者手数详情"
                    )
                    logger.info(f"喊单者手数验证通过: {lots_open}")

                with allure.step("交易币种校验"):
                    master_symbol = self.json_utils.extract(response.json(),
                                                            "$.result.records[0].master_symbol")
                    symbol = var_manager.get_variable("symbol")

                    self.verify_data(
                        actual_value=master_symbol,
                        expected_value=symbol,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"交易币种符合预期",
                        attachment_name="交易币种详情"
                    )
                    logger.info(f"交易币种验证通过: {master_symbol}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-开仓日志-开平仓明细-开仓后")
        def test_query_opentrader_detail(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                ticket_open = var_manager.get_variable("ticket_open")
                params = {
                    "_t": current_timestamp_seconds,
                    "pageNo": 1,
                    "pageSize": 20,
                    "self_master_ticket": ticket_open
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgreport/api/getColumnsAndData/1568899025974796289',
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
                slave_ticket_list = self.json_utils.extract(
                    response.json(),
                    "$.result.data.records[0].slave_ticket",
                    default=[],
                    multi_match=True
                )
                follow_account = var_manager.get_variable("follow_account")
                if not slave_ticket_list:
                    attach_body = f"跟单账号：{follow_account}，返回的slave_ticket列表为空（暂无数据）"
                else:
                    attach_body = f"跟单账号：{follow_account}，返回 {len(slave_ticket_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"跟单账号：{follow_account}结果",
                    attachment_type="text/plain"
                )

                for idx, slave_ticket in enumerate(slave_ticket_list):
                    order_no = var_manager.get_variable("order_no")
                    self.verify_data(
                        actual_value=slave_ticket,
                        expected_value=order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的订单号应为{slave_ticket}",
                        attachment_name=f"跟单账户:{follow_account}第 {idx + 1} 条记录校验"
                    )

                with allure.step("喊单者订单号校验"):
                    master_ticket = self.json_utils.extract(response.json(),
                                                            "$.result.data.records[0].master_ticket")
                    ticket_open = var_manager.get_variable("ticket_open")

                    self.verify_data(
                        actual_value=master_ticket,
                        expected_value=ticket_open,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"喊单者订单号符合预期",
                        attachment_name="喊单者订单号详情"
                    )
                    logger.info(f"喊单者订单号验证通过: {master_ticket}")

                with allure.step("喊单者手数校验"):
                    master_lots = self.json_utils.extract(response.json(),
                                                          "$.result.data.records[0].master_lots")
                    lots_open = var_manager.get_variable("lots_open")

                    self.verify_data(
                        actual_value=float(master_lots),
                        expected_value=float(lots_open),
                        op=CompareOp.EQ,
                        message=f"喊单者手数符合预期",
                        attachment_name="喊单者手数详情"
                    )
                    logger.info(f"喊单者手数验证通过: {master_lots}")

                with allure.step("跟单手数校验"):
                    slave_lots = self.json_utils.extract(response.json(),
                                                         "$.result.data.records[0].slave_lots")
                    if not slave_lots:
                        allure.attach("跟单手数返回为空", "跟单手数详情", allure.attachment_type.TEXT)
                    else:
                        lots_open = var_manager.get_variable("lots_open")
                        follow_periodP = var_manager.get_variable("follow_periodP")
                        trader_periodP = var_manager.get_variable("trader_periodP")
                        # 获取跟单净值比例
                        fixed_proportion = var_manager.get_variable("fixed_proportion")
                        # 百分比数据转换
                        follow_fixed_decimal = percentage_to_decimal(fixed_proportion)
                        expected_lots_open = lots_open * (follow_periodP / trader_periodP) * follow_fixed_decimal
                        # 四舍五入保留两位小数
                        expected_lots_open = round(expected_lots_open, 2)

                        # 最小手数限制（0.01）
                        min_order_size = 0.01
                        if expected_lots_open < min_order_size:
                            allure.attach(
                                f"计算预期手数{expected_lots_open} < 最小手数{min_order_size}，强制重置为{min_order_size}",
                                "预期手数调整说明", allure.attachment_type.TEXT)
                            expected_lots_open = min_order_size

                        self.verify_data(
                            actual_value=float(slave_lots),
                            expected_value=float(expected_lots_open),
                            op=CompareOp.EQ,
                            message=f"跟单手数符合预期",
                            attachment_name="跟单手数详情"
                        )
                        logger.info(f"跟单手数验证通过: {slave_lots}")

                with allure.step("交易币种校验"):
                    master_symbol = self.json_utils.extract(response.json(),
                                                            "$.result.data.records[0].master_symbol")
                    symbol = var_manager.get_variable("symbol")

                    self.verify_data(
                        actual_value=master_symbol,
                        expected_value=symbol,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"交易币种符合预期",
                        attachment_name="交易币种详情"
                    )
                    logger.info(f"交易币种验证通过: {master_symbol}")

                # @pytest.mark.skipif(True, reason="跳过此用例")

        @pytest.mark.retry(n=3, delay=10)
        @allure.title("跟单管理-VPS管理-喊单者账号-开仓后")
        def test_query_opentrader_getRecordList(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_account = var_manager.get_variable("trader_account")
                vpsrunIpAddr = var_manager.get_variable("vpsrunIpAddr")
                params = {
                    "_t": current_timestamp_seconds,
                    "pageNo": "1",
                    "pageSize": "50",
                    "accountLike": trader_account,
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
                with allure.step("喊单者手数校验-MT4开仓手数和持仓订单手数"):
                    totalLots = self.json_utils.extract(response.json(), "$.records[0].totalLots")
                    logging.info(f"手数是: {totalLots}")

                    lots_open = var_manager.get_variable("lots_open")

                    self.verify_data(
                        actual_value=float(totalLots),
                        expected_value=float(lots_open),
                        op=CompareOp.EQ,
                        message=f"手数符合预期",
                        attachment_name="手数详情"
                    )
                    logger.info(f"喊单者手数：{totalLots} MT4开仓手数：{lots_open}")

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
                    if not totalLots:
                        allure.attach("跟单手数为空", "跟单手数详情", allure.attachment_type.TEXT)
                    else:
                        lots_open = var_manager.get_variable("lots_open")
                        follow_periodP = var_manager.get_variable("follow_periodP")
                        trader_periodP = var_manager.get_variable("trader_periodP")
                        # 获取跟单净值比例
                        fixed_proportion = var_manager.get_variable("fixed_proportion")
                        # 百分比数据转换
                        follow_fixed_decimal = percentage_to_decimal(fixed_proportion)
                        expected_lots_open = lots_open * (follow_periodP / trader_periodP) * follow_fixed_decimal
                        # 四舍五入保留两位小数
                        expected_lots_open = round(expected_lots_open, 2)

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
                        logger.info(f"跟单者手数：{totalLots}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("MT4平台平仓操作")
        def test_mt4_close(self, var_manager, db_transaction):
            # 实例化类
            public_front = PublicUtils()

            # MT4平台平仓操作
            public_front.test_mt4_close(var_manager, db_transaction)

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
                            message=f"订单号数据正确",
                            attachment_name="订单号详情"
                        )
                        logger.info(f"订单号数据正确,开仓订单号：{ticket_open} 喊单者订单号：{order_no}")

                    with allure.step("喊单手数校验-MT4开仓手数和持仓订单手数"):
                        order_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                        logging.info(f"喊单者手数是: {order_size}")

                        lots_open = var_manager.get_variable("lots_open")
                        self.verify_data(
                            actual_value=float(order_size),
                            expected_value=float(lots_open),
                            op=CompareOp.EQ,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"喊单者手数：{order_size} MT4开仓手数：{lots_open}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("账号管理-历史订单-跟单MT4账户查询-平仓后")
        def test_query_follow_id(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_pass_id = var_manager.get_variable("follow_pass_id")
                follow_account = var_manager.get_variable("follow_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "trader_id": follow_pass_id,
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

            with allure.step("3. 提取数据"):
                order_no = self.json_utils.extract(response.json(), "$.result.records[0].order_no")
                var_manager.set_runtime_variable("order_no", order_no)
                allure.attach(f"{order_no}", "跟单订单号", allure.attachment_type.TEXT)

            with allure.step(f"3. 查询校验"):
                trader_id_list = self.json_utils.extract(
                    response.json(),
                    "$.result.records[0].trader_id",
                    default=[],
                    multi_match=True
                )

                if not trader_id_list:
                    attach_body = f"MT4账号查询[{follow_account}]，返回的trader_id列表为空（暂无数据）"
                else:
                    attach_body = f"MT4账号查询[{follow_account}]，返回 {len(trader_id_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"账号ID:{follow_account}查询结果",
                    attachment_type="text/plain"
                )

                for idx, trader_id in enumerate(trader_id_list):
                    self.verify_data(
                        actual_value=int(trader_id),
                        expected_value=int(follow_pass_id),
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的账号ID应为{trader_id}",
                        attachment_name=f"账号ID:{follow_pass_id}第 {idx + 1} 条记录校验"
                    )

                with allure.step("喊单者订单号校验"):
                    master_order_no = self.json_utils.extract(response.json(),
                                                              "$.result.records[0].master_order_no")
                    ticket_open = var_manager.get_variable("ticket_open")

                    self.verify_data(
                        actual_value=ticket_open,
                        expected_value=master_order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"订单号数据正确",
                        attachment_name="订单号详情"
                    )
                    logger.info(f"订单号数据正确,开仓订单号：{ticket_open} 喊单者订单号：{master_order_no}")

                with allure.step("跟单订单号校验"):
                    slave_ticket = var_manager.get_variable("slave_ticket")
                    self.verify_data(
                        actual_value=slave_ticket,
                        expected_value=order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"订单号数据正确",
                        attachment_name="订单号详情"
                    )
                    logger.info(f"订单号数据正确,跟单者订单号：{order_no} 数据库数据：{slave_ticket}")

                with allure.step("跟单手数校验"):
                    add_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                    if not add_size:
                        allure.attach("订单手数数据为空", "订单手数数据", allure.attachment_type.TEXT)
                    else:
                        lots_open = var_manager.get_variable("lots_open")
                        follow_periodP = var_manager.get_variable("follow_periodP")
                        trader_periodP = var_manager.get_variable("trader_periodP")
                        # 获取跟单净值比例
                        fixed_proportion = var_manager.get_variable("fixed_proportion")
                        # 百分比数据转换
                        follow_fixed_decimal = percentage_to_decimal(fixed_proportion)
                        expected_lots_open = lots_open * (follow_periodP / trader_periodP) * follow_fixed_decimal
                        # 四舍五入保留两位小数
                        expected_lots_open = round(expected_lots_open, 2)

                        # 最小手数限制（0.01）
                        min_order_size = 0.01
                        if expected_lots_open < min_order_size:
                            allure.attach(
                                f"计算预期手数{expected_lots_open} < 最小手数{min_order_size}，强制重置为{min_order_size}",
                                "预期手数调整说明", allure.attachment_type.TEXT)
                            expected_lots_open = min_order_size

                        self.verify_data(
                            actual_value=float(add_size),
                            expected_value=float(expected_lots_open),
                            op=CompareOp.EQ,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"跟单者手数：{add_size}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-开仓日志-开平仓明细-平仓后")
        def test_query_closetrader_detail(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                ticket_open = var_manager.get_variable("ticket_open")
                params = {
                    "_t": current_timestamp_seconds,
                    "pageNo": 1,
                    "pageSize": 20,
                    "self_master_ticket": ticket_open
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgreport/api/getColumnsAndData/1568899025974796289',
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
                slave_ticket_list = self.json_utils.extract(
                    response.json(),
                    "$.result.data.records[0].slave_ticket",
                    default=[],
                    multi_match=True
                )
                follow_account = var_manager.get_variable("follow_account")
                if not slave_ticket_list:
                    attach_body = f"跟单账号：{follow_account}，返回的slave_ticket列表为空（暂无数据）"
                else:
                    attach_body = f"跟单账号：{follow_account}，返回 {len(slave_ticket_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"跟单账号：{follow_account}结果",
                    attachment_type="text/plain"
                )

                for idx, slave_ticket in enumerate(slave_ticket_list):
                    order_no = var_manager.get_variable("order_no")
                    self.verify_data(
                        actual_value=slave_ticket,
                        expected_value=order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的订单号应为{slave_ticket}",
                        attachment_name=f"跟单账户:{follow_account}第 {idx + 1} 条记录校验"
                    )

                with allure.step("喊单者订单号校验"):
                    master_ticket = self.json_utils.extract(response.json(),
                                                            "$.result.data.records[0].master_ticket")
                    ticket_open = var_manager.get_variable("ticket_open")

                    self.verify_data(
                        actual_value=master_ticket,
                        expected_value=ticket_open,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"喊单者订单号符合预期",
                        attachment_name="喊单者订单号详情"
                    )
                    logger.info(f"喊单者订单号验证通过: {master_ticket}")

                with allure.step("喊单者手数校验"):
                    master_lots = self.json_utils.extract(response.json(),
                                                          "$.result.data.records[0].master_lots")
                    lots_open = var_manager.get_variable("lots_open")

                    self.verify_data(
                        actual_value=float(master_lots),
                        expected_value=float(lots_open),
                        op=CompareOp.EQ,
                        message=f"喊单者手数符合预期",
                        attachment_name="喊单者手数详情"
                    )
                    logger.info(f"喊单者手数验证通过: {master_lots}")

                with allure.step("跟单手数校验"):
                    slave_lots = self.json_utils.extract(response.json(),
                                                         "$.result.data.records[0].slave_lots")
                    if not slave_lots:
                        allure.attach("跟单手数为空", "跟单手数详情", allure.attachment_type.TEXT)
                    else:
                        lots_open = var_manager.get_variable("lots_open")
                        follow_periodP = var_manager.get_variable("follow_periodP")
                        trader_periodP = var_manager.get_variable("trader_periodP")
                        # 获取跟单净值比例
                        fixed_proportion = var_manager.get_variable("fixed_proportion")
                        # 百分比数据转换
                        follow_fixed_decimal = percentage_to_decimal(fixed_proportion)
                        expected_lots_open = lots_open * (follow_periodP / trader_periodP) * follow_fixed_decimal
                        # 四舍五入保留两位小数
                        expected_lots_open = round(expected_lots_open, 2)

                        # 最小手数限制（0.01）
                        min_order_size = 0.01
                        if expected_lots_open < min_order_size:
                            allure.attach(
                                f"计算预期手数{expected_lots_open} < 最小手数{min_order_size}，强制重置为{min_order_size}",
                                "预期手数调整说明", allure.attachment_type.TEXT)
                            expected_lots_open = min_order_size

                        self.verify_data(
                            actual_value=float(slave_lots),
                            expected_value=float(expected_lots_open),
                            op=CompareOp.EQ,
                            message=f"跟单手数符合预期",
                            attachment_name="跟单手数详情"
                        )
                        logger.info(f"跟单手数验证通过: {slave_lots}")

                with allure.step("交易币种校验"):
                    master_symbol = self.json_utils.extract(response.json(),
                                                            "$.result.data.records[0].master_symbol")
                    symbol = var_manager.get_variable("symbol")

                    self.verify_data(
                        actual_value=master_symbol,
                        expected_value=symbol,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"交易币种符合预期",
                        attachment_name="交易币种详情"
                    )
                    logger.info(f"交易币种验证通过: {master_symbol}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库提取数据-平仓时间差")
        def test_dbquery_closeorder(self, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否新增成功"):
                ticket_open = var_manager.get_variable("ticket_open")

                # 优化后的数据库查询
                db_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM bchain_trader_subscribe_order WHERE master_ticket = %s",
                    (ticket_open,),
                )

                # 提取数据库中的值
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

            with allure.step("2. 提取数据库中的值"):
                slave_ticket = db_data[0]["slave_ticket"]
                print(f"输出：{slave_ticket}")
                logging.info(f"跟单账号订单号: {slave_ticket}")
                var_manager.set_runtime_variable("slave_ticket", slave_ticket)

                close_time_difference = db_data[0]["close_time_difference"]
                print(f"输出：{close_time_difference}")
                logging.info(f"平仓时间差（毫秒）: {close_time_difference}")
                var_manager.set_runtime_variable("close_time_difference", close_time_difference)
                allure.attach(f"平仓时间差（毫秒）: {close_time_difference}", "平仓时间差")

    @allure.story("场景3：跟随方式-按净值-1%")
    @allure.description("""
    ### 测试说明
    - 前置条件：有喊单账号、跟单账号，跟单已经和喊单有订阅关系
      1. 修改订阅信息，跟随方式-按净值-1%
      2. MT4进行登录，然后进行开仓，总手数0.01
      3. 账号管理-持仓订单-喊单和跟单数据校验
      4. 跟单管理-开仓日志-喊单和跟单数据校验
      5. 跟单管理-VPS管理-喊单和跟单数据校验
      6. MT4进行平仓
      7. 账号管理-历史订单-喊单和跟单数据校验
      8. 跟单管理-开仓日志-喊单和跟单数据校验
    - 预期结果：喊单和跟单数据校验正确
    """)
    # @pytest.mark.skipif(True, reason="跳过此用例")
    class Test_orderseng3(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-实时跟单-修改订阅数据")
        def test_query_updata_editPa(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_jeecg_rowkey = var_manager.get_variable("follow_jeecg_rowkey")
                data = {
                    "id": follow_jeecg_rowkey,
                    "direction": "FORWARD",
                    "followingMode": 4,
                    "fixedProportion": 1,
                    "fixedLots": None
                }
                response = self.send_put_request(
                    logged_session,
                    '/blockchain/master-slave/editPa',
                    json_data=data
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-实时跟单-订阅列表数据")
        def test_query_getColumnsAndData(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_account = var_manager.get_variable("follow_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "account": follow_account,
                    "pageNo": "1",
                    "pageSize": "20",
                    "status": "NORMAL,AUDIT"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )
            with allure.step("3. 提取数据"):
                fixed_proportion = self.json_utils.extract(response.json(),
                                                           "$.result.data.records[0].fixed_proportion")
                var_manager.set_runtime_variable("fixed_proportion", fixed_proportion)

        @pytest.mark.retry(n=3, delay=10)
        @allure.title("跟单管理-VPS管理-提取喊单者净值")
        def test_query_get_traderquit(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_account = var_manager.get_variable("trader_account")
                vpsrunIpAddr = var_manager.get_variable("vpsrunIpAddr")
                params = {
                    "_t": current_timestamp_seconds,
                    "pageNo": "1",
                    "pageSize": "50",
                    "accountLike": trader_account,
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

            with allure.step(f"3. 提取净值数据"):
                trader_equity = self.json_utils.extract(response.json(), "$.records[0].equity")
                currency = self.json_utils.extract(response.json(), "$.records[0].currency")

                if currency == "USD":
                    trader_periodP = round(float(trader_equity) * 1.0, 2)
                elif currency == "JPY":
                    trader_periodP = round(float(trader_equity) * 0.00672, 2)
                elif currency == "AUD":
                    trader_periodP = round(float(trader_equity) * 0.6251, 2)
                elif currency == "USC":
                    trader_periodP = round(float(trader_equity) * 0.01, 2)
                else:
                    pytest.fail(f"不支持的币种：{currency}，请补充币种转换逻辑")

                logging.info(f"币种的转换详情,当前币种{currency}，转换前：{trader_equity},转换后：{trader_periodP}")
                allure.attach(f"当前币种{currency}，转换前：{trader_equity},转换后：{trader_periodP}",
                              "币种类型转换详情", allure.attachment_type.TEXT)
                var_manager.set_runtime_variable("trader_periodP", trader_periodP)

        @allure.title("跟单管理-VPS管理-提取跟单者净值")
        def test_query_get_followquit(self, var_manager, logged_session):
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

            with allure.step(f"3. 提取净值数据"):
                follow_equity = self.json_utils.extract(response.json(), "$.records[0].equity")
                currency = self.json_utils.extract(response.json(), "$.records[0].currency")

                if currency == "USD":
                    follow_periodP = round(float(follow_equity) * 1.0, 2)
                elif currency == "JPY":
                    follow_periodP = round(float(follow_equity) * 0.00672, 2)
                elif currency == "AUD":
                    follow_periodP = round(float(follow_equity) * 0.6251, 2)
                elif currency == "USC":
                    follow_periodP = round(float(follow_equity) * 0.01, 2)
                else:
                    pytest.fail(f"不支持的币种：{currency}，请补充币种转换逻辑")

                logging.info(f"币种的转换详情,当前币种{currency}，转换前：{follow_equity},转换后：{follow_periodP}")
                allure.attach(f"当前币种{currency}，转换前：{follow_equity},转换后：{follow_periodP}",
                              "币种类型转换详情", allure.attachment_type.TEXT)
                var_manager.set_runtime_variable("follow_periodP", follow_periodP)

        @allure.title("公共方法-校验前操作")
        def test_run_public(self, var_manager, logged_session):
            # 实例化类
            public_front = PublicUtils()

            # 按顺序调用
            # 登录获取 token
            public_front.test_login(var_manager)
            # 平仓喊单账号
            public_front.test_close_trader(var_manager)
            # 平仓跟单账号
            public_front.test_close_follow(var_manager)
            # 清理魔术号相关数据
            public_front.test_query_magic(var_manager, logged_session)
            # 清理账号ID相关数据
            public_front.test_query_follow_passid(var_manager, logged_session)
            # 登录MT4账号获取token
            public_front.test_mt4_login(var_manager)
            # MT4平台开仓操作
            public_front.test_mt4_open(var_manager)

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @pytest.mark.retry(n=3, delay=5)
        @allure.title("账号管理-持仓订单-喊单者账号ID查询-开仓后")
        def test_query_opentrader_passid(self, var_manager, logged_session):
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
                    '/online/cgform/api/getData/402883977b38c9ca017b38c9caff0000',
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
                    attach_body = f"账号ID查询[{trader_account}]，返回的trader_id列表为空（暂无数据）"
                else:
                    attach_body = f"账号ID查询[{trader_account}]，返回 {len(trader_id_list)} 条记录"

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
                            message=f"订单号数据正确",
                            attachment_name="订单号详情"
                        )
                        logger.info(f"订单号数据正确,开仓订单号：{ticket_open} 喊单者订单号：{order_no}")

                    with allure.step("喊单手数校验-MT4开仓手数和持仓订单手数"):
                        order_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                        logging.info(f"喊单者手数是: {order_size}")

                        lots_open = var_manager.get_variable("lots_open")

                        self.verify_data(
                            actual_value=float(order_size),
                            expected_value=float(lots_open),
                            op=CompareOp.EQ,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"喊单者手数：{order_size} MT4开仓手数：{lots_open}")

                    with allure.step("喊单的订单方向校验"):
                        type = self.json_utils.extract(response.json(), "$.result.records[0].type")
                        logging.info(f"喊单者方向是: {type}")

                        self.verify_data(
                            actual_value=float(type),
                            expected_value=float(0),
                            op=CompareOp.EQ,
                            message=f"喊单者方向符合预期",
                            attachment_name="喊单者方向详情"
                        )
                        logger.info(f"喊单者方向：{type}")
                        allure.attach("0:buy  1:sell", "方向解释", allure.attachment_type.TEXT)

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库提取数据-提取跟单订单号")
        def test_dbquery_openorder(self, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否新增成功"):
                ticket_open = var_manager.get_variable("ticket_open")

                # 优化后的数据库查询
                db_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM bchain_trader_subscribe_order WHERE master_ticket = %s",
                    (ticket_open,),
                )

                # 提取数据库中的值
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

            with allure.step("2. 提取数据库中的值"):
                slave_ticket = db_data[0]["slave_ticket"]
                print(f"输出：{slave_ticket}")
                logging.info(f"跟单账号订单号: {slave_ticket}")
                var_manager.set_runtime_variable("slave_ticket", slave_ticket)

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("账号管理-持仓订单-跟单账号ID查询-开仓后")
        def test_query_openfollow_passid(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_pass_id = var_manager.get_variable("follow_pass_id")
                follow_account = var_manager.get_variable("follow_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "trader_id": follow_pass_id,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 20,
                    "superQueryMatchType": "and"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/402883977b38c9ca017b38c9caff0000',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 提取数据"):
                order_no = self.json_utils.extract(response.json(), "$.result.records[0].order_no")
                var_manager.set_runtime_variable("order_no", order_no)
                allure.attach(f"{order_no}", "跟单订单号", allure.attachment_type.TEXT)

            with allure.step(f"3. 查询校验"):
                trader_id_list = self.json_utils.extract(
                    response.json(),
                    "$.result.records[0].trader_id",
                    default=[],
                    multi_match=True
                )

                if not trader_id_list:
                    attach_body = f"账号ID查询[{follow_account}]，返回的trader_id列表为空（暂无数据）"
                else:
                    attach_body = f"账号ID查询[{follow_account}]，返回 {len(trader_id_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"账号ID:{follow_account}查询结果",
                    attachment_type="text/plain"
                )

                for idx, trader_id in enumerate(trader_id_list):
                    self.verify_data(
                        actual_value=int(trader_id),
                        expected_value=int(follow_pass_id),
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的账号ID应为{trader_id}",
                        attachment_name=f"账号ID:{follow_pass_id}第 {idx + 1} 条记录校验"
                    )

                with allure.step("喊单者订单号校验"):
                    master_order_no = self.json_utils.extract(response.json(), "$.result.records[0].master_order_no")
                    ticket_open = var_manager.get_variable("ticket_open")

                    self.verify_data(
                        actual_value=ticket_open,
                        expected_value=master_order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"订单号数据正确",
                        attachment_name="订单号详情"
                    )
                    logger.info(f"订单号数据正确,开仓订单号：{ticket_open} 喊单者订单号：{master_order_no}")

                with allure.step("跟单订单号校验"):
                    slave_ticket = var_manager.get_variable("slave_ticket")
                    self.verify_data(
                        actual_value=slave_ticket,
                        expected_value=order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"订单号数据正确",
                        attachment_name="订单号详情"
                    )
                    logger.info(f"订单号数据正确,跟单者订单号：{order_no} 数据库数据：{slave_ticket}")

                with allure.step("跟单手数校验"):
                    add_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                    if not add_size:
                        allure.attach("订单手数数据为空", "订单手数数据", allure.attachment_type.TEXT)
                    else:
                        lots_open = var_manager.get_variable("lots_open")
                        follow_periodP = var_manager.get_variable("follow_periodP")
                        trader_periodP = var_manager.get_variable("trader_periodP")
                        # 获取跟单净值比例
                        fixed_proportion = var_manager.get_variable("fixed_proportion")
                        # 百分比数据转换
                        follow_fixed_decimal = percentage_to_decimal(fixed_proportion)
                        expected_lots_open = lots_open * (follow_periodP / trader_periodP) * follow_fixed_decimal

                        # 最小手数限制（0.01）
                        min_order_size = 0.01
                        if expected_lots_open < min_order_size:
                            allure.attach(
                                f"计算预期手数{expected_lots_open} < 最小手数{min_order_size}，强制重置为{min_order_size}",
                                "预期手数调整说明", allure.attachment_type.TEXT)
                            expected_lots_open = min_order_size

                        self.verify_data(
                            actual_value=float(add_size),
                            expected_value=float(expected_lots_open),
                            op=CompareOp.EQ,
                            abs_tol=0.01,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"跟单者手数：{add_size}")

                with allure.step("跟单的订单方向校验"):
                    type = self.json_utils.extract(response.json(), "$.result.records[0].type")
                    logging.info(f"跟单方向是: {type}")

                    self.verify_data(
                        actual_value=float(type),
                        expected_value=float(0),
                        op=CompareOp.EQ,
                        message=f"跟单方向符合预期",
                        attachment_name="跟单方向详情"
                    )
                    logger.info(f"跟单方向：{type}")
                    allure.attach("0:buy  1:sell", "方向解释", allure.attachment_type.TEXT)

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-开仓日志-喊单账户查询-开仓后")
        def test_query_opentrader_getdata(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_account = var_manager.get_variable("trader_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "master_account": trader_account,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 20,
                    "superQueryMatchType": "and"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/2c934301834efb6801834efbe1ba0002',
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
                master_ticket_list = self.json_utils.extract(
                    response.json(),
                    "$.result.records[0].master_ticket",
                    default=[],
                    multi_match=True
                )

                if not master_ticket_list:
                    attach_body = f"喊单账户查询[{trader_account}]，返回的master_ticket列表为空（暂无数据）"
                else:
                    attach_body = f"喊单账户查询[{trader_account}]，返回 {len(master_ticket_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"喊单账户:{trader_account}查询结果",
                    attachment_type="text/plain"
                )

                for idx, master_ticket in enumerate(master_ticket_list):
                    ticket_open = var_manager.get_variable("ticket_open")
                    self.verify_data(
                        actual_value=master_ticket,
                        expected_value=ticket_open,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的订单号应为{master_ticket}",
                        attachment_name=f"喊单账户:{trader_account}第 {idx + 1} 条记录校验"
                    )

                with allure.step("喊单者手数校验"):
                    master_lots = self.json_utils.extract(response.json(),
                                                          "$.result.records[0].master_lots")
                    lots_open = var_manager.get_variable("lots_open")

                    self.verify_data(
                        actual_value=float(master_lots),
                        expected_value=float(lots_open),
                        op=CompareOp.EQ,
                        message=f"喊单者手数符合预期",
                        attachment_name="喊单者手数详情"
                    )
                    logger.info(f"喊单者手数验证通过: {lots_open}")

                with allure.step("交易币种校验"):
                    master_symbol = self.json_utils.extract(response.json(),
                                                            "$.result.records[0].master_symbol")
                    symbol = var_manager.get_variable("symbol")

                    self.verify_data(
                        actual_value=master_symbol,
                        expected_value=symbol,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"交易币种符合预期",
                        attachment_name="交易币种详情"
                    )
                    logger.info(f"交易币种验证通过: {master_symbol}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-开仓日志-开平仓明细-开仓后")
        def test_query_opentrader_detail(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                ticket_open = var_manager.get_variable("ticket_open")
                params = {
                    "_t": current_timestamp_seconds,
                    "pageNo": 1,
                    "pageSize": 20,
                    "self_master_ticket": ticket_open
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgreport/api/getColumnsAndData/1568899025974796289',
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
                slave_ticket_list = self.json_utils.extract(
                    response.json(),
                    "$.result.data.records[0].slave_ticket",
                    default=[],
                    multi_match=True
                )
                follow_account = var_manager.get_variable("follow_account")
                if not slave_ticket_list:
                    attach_body = f"跟单账号：{follow_account}，返回的slave_ticket列表为空（暂无数据）"
                else:
                    attach_body = f"跟单账号：{follow_account}，返回 {len(slave_ticket_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"跟单账号：{follow_account}结果",
                    attachment_type="text/plain"
                )

                for idx, slave_ticket in enumerate(slave_ticket_list):
                    order_no = var_manager.get_variable("order_no")
                    self.verify_data(
                        actual_value=slave_ticket,
                        expected_value=order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的订单号应为{slave_ticket}",
                        attachment_name=f"跟单账户:{follow_account}第 {idx + 1} 条记录校验"
                    )

                with allure.step("喊单者订单号校验"):
                    master_ticket = self.json_utils.extract(response.json(),
                                                            "$.result.data.records[0].master_ticket")
                    ticket_open = var_manager.get_variable("ticket_open")

                    self.verify_data(
                        actual_value=master_ticket,
                        expected_value=ticket_open,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"喊单者订单号符合预期",
                        attachment_name="喊单者订单号详情"
                    )
                    logger.info(f"喊单者订单号验证通过: {master_ticket}")

                with allure.step("喊单者手数校验"):
                    master_lots = self.json_utils.extract(response.json(),
                                                          "$.result.data.records[0].master_lots")
                    lots_open = var_manager.get_variable("lots_open")

                    self.verify_data(
                        actual_value=float(master_lots),
                        expected_value=float(lots_open),
                        op=CompareOp.EQ,
                        message=f"喊单者手数符合预期",
                        attachment_name="喊单者手数详情"
                    )
                    logger.info(f"喊单者手数验证通过: {master_lots}")

                with allure.step("跟单手数校验"):
                    slave_lots = self.json_utils.extract(response.json(),
                                                         "$.result.data.records[0].slave_lots")
                    if not slave_lots:
                        allure.attach("跟单手数返回为空", "跟单手数详情", allure.attachment_type.TEXT)
                    else:
                        lots_open = var_manager.get_variable("lots_open")
                        follow_periodP = var_manager.get_variable("follow_periodP")
                        trader_periodP = var_manager.get_variable("trader_periodP")
                        # 获取跟单净值比例
                        fixed_proportion = var_manager.get_variable("fixed_proportion")
                        # 百分比数据转换
                        follow_fixed_decimal = percentage_to_decimal(fixed_proportion)
                        expected_lots_open = lots_open * (follow_periodP / trader_periodP) * follow_fixed_decimal

                        # 最小手数限制（0.01）
                        min_order_size = 0.01
                        if expected_lots_open < min_order_size:
                            allure.attach(
                                f"计算预期手数{expected_lots_open} < 最小手数{min_order_size}，强制重置为{min_order_size}",
                                "预期手数调整说明", allure.attachment_type.TEXT)
                            expected_lots_open = min_order_size

                        self.verify_data(
                            actual_value=float(slave_lots),
                            expected_value=float(expected_lots_open),
                            op=CompareOp.EQ,
                            abs_tol=0.01,
                            message=f"跟单手数符合预期",
                            attachment_name="跟单手数详情"
                        )
                        logger.info(f"跟单手数验证通过: {slave_lots}")

                with allure.step("交易币种校验"):
                    master_symbol = self.json_utils.extract(response.json(),
                                                            "$.result.data.records[0].master_symbol")
                    symbol = var_manager.get_variable("symbol")

                    self.verify_data(
                        actual_value=master_symbol,
                        expected_value=symbol,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"交易币种符合预期",
                        attachment_name="交易币种详情"
                    )
                    logger.info(f"交易币种验证通过: {master_symbol}")

                # @pytest.mark.skipif(True, reason="跳过此用例")

        @pytest.mark.retry(n=3, delay=10)
        @allure.title("跟单管理-VPS管理-喊单者账号-开仓后")
        def test_query_opentrader_getRecordList(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_account = var_manager.get_variable("trader_account")
                vpsrunIpAddr = var_manager.get_variable("vpsrunIpAddr")
                params = {
                    "_t": current_timestamp_seconds,
                    "pageNo": "1",
                    "pageSize": "50",
                    "accountLike": trader_account,
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
                with allure.step("喊单者手数校验-MT4开仓手数和持仓订单手数"):
                    totalLots = self.json_utils.extract(response.json(), "$.records[0].totalLots")
                    logging.info(f"手数是: {totalLots}")

                    lots_open = var_manager.get_variable("lots_open")

                    self.verify_data(
                        actual_value=float(totalLots),
                        expected_value=float(lots_open),
                        op=CompareOp.EQ,
                        message=f"手数符合预期",
                        attachment_name="手数详情"
                    )
                    logger.info(f"喊单者手数：{totalLots} MT4开仓手数：{lots_open}")

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
                    if not totalLots:
                        allure.attach("跟单手数为空", "跟单手数详情", allure.attachment_type.TEXT)
                    else:
                        lots_open = var_manager.get_variable("lots_open")
                        follow_periodP = var_manager.get_variable("follow_periodP")
                        trader_periodP = var_manager.get_variable("trader_periodP")
                        # 获取跟单净值比例
                        fixed_proportion = var_manager.get_variable("fixed_proportion")
                        # 百分比数据转换
                        follow_fixed_decimal = percentage_to_decimal(fixed_proportion)
                        expected_lots_open = lots_open * (follow_periodP / trader_periodP) * follow_fixed_decimal

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
                            abs_tol=0.01,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"跟单者手数：{totalLots}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("MT4平台平仓操作")
        def test_mt4_close(self, var_manager, db_transaction):
            # 实例化类
            public_front = PublicUtils()

            # MT4平台平仓操作
            public_front.test_mt4_close(var_manager, db_transaction)

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
                            message=f"订单号数据正确",
                            attachment_name="订单号详情"
                        )
                        logger.info(f"订单号数据正确,开仓订单号：{ticket_open} 喊单者订单号：{order_no}")

                    with allure.step("喊单手数校验-MT4开仓手数和持仓订单手数"):
                        order_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                        logging.info(f"喊单者手数是: {order_size}")

                        lots_open = var_manager.get_variable("lots_open")
                        self.verify_data(
                            actual_value=float(order_size),
                            expected_value=float(lots_open),
                            op=CompareOp.EQ,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"喊单者手数：{order_size} MT4开仓手数：{lots_open}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("账号管理-历史订单-跟单MT4账户查询-平仓后")
        def test_query_follow_id(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_pass_id = var_manager.get_variable("follow_pass_id")
                follow_account = var_manager.get_variable("follow_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "trader_id": follow_pass_id,
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

            with allure.step("3. 提取数据"):
                order_no = self.json_utils.extract(response.json(), "$.result.records[0].order_no")
                var_manager.set_runtime_variable("order_no", order_no)
                allure.attach(f"{order_no}", "跟单订单号", allure.attachment_type.TEXT)

            with allure.step(f"3. 查询校验"):
                trader_id_list = self.json_utils.extract(
                    response.json(),
                    "$.result.records[0].trader_id",
                    default=[],
                    multi_match=True
                )

                if not trader_id_list:
                    attach_body = f"MT4账号查询[{follow_account}]，返回的trader_id列表为空（暂无数据）"
                else:
                    attach_body = f"MT4账号查询[{follow_account}]，返回 {len(trader_id_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"账号ID:{follow_account}查询结果",
                    attachment_type="text/plain"
                )

                for idx, trader_id in enumerate(trader_id_list):
                    self.verify_data(
                        actual_value=int(trader_id),
                        expected_value=int(follow_pass_id),
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的账号ID应为{trader_id}",
                        attachment_name=f"账号ID:{follow_pass_id}第 {idx + 1} 条记录校验"
                    )

                with allure.step("喊单者订单号校验"):
                    master_order_no = self.json_utils.extract(response.json(),
                                                              "$.result.records[0].master_order_no")
                    ticket_open = var_manager.get_variable("ticket_open")

                    self.verify_data(
                        actual_value=ticket_open,
                        expected_value=master_order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"订单号数据正确",
                        attachment_name="订单号详情"
                    )
                    logger.info(f"订单号数据正确,开仓订单号：{ticket_open} 喊单者订单号：{master_order_no}")

                with allure.step("跟单订单号校验"):
                    slave_ticket = var_manager.get_variable("slave_ticket")
                    self.verify_data(
                        actual_value=slave_ticket,
                        expected_value=order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"订单号数据正确",
                        attachment_name="订单号详情"
                    )
                    logger.info(f"订单号数据正确,跟单者订单号：{order_no} 数据库数据：{slave_ticket}")

                with allure.step("跟单手数校验"):
                    add_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                    if not add_size:
                        allure.attach("订单手数数据为空", "订单手数数据", allure.attachment_type.TEXT)
                    else:
                        lots_open = var_manager.get_variable("lots_open")
                        follow_periodP = var_manager.get_variable("follow_periodP")
                        trader_periodP = var_manager.get_variable("trader_periodP")
                        # 获取跟单净值比例
                        fixed_proportion = var_manager.get_variable("fixed_proportion")
                        # 百分比数据转换
                        follow_fixed_decimal = percentage_to_decimal(fixed_proportion)
                        expected_lots_open = lots_open * (follow_periodP / trader_periodP) * follow_fixed_decimal
                        # 四舍五入保留两位小数
                        expected_lots_open = round(expected_lots_open, 2)

                        # 最小手数限制（0.01）
                        min_order_size = 0.01
                        if expected_lots_open < min_order_size:
                            allure.attach(
                                f"计算预期手数{expected_lots_open} < 最小手数{min_order_size}，强制重置为{min_order_size}",
                                "预期手数调整说明", allure.attachment_type.TEXT)
                            expected_lots_open = min_order_size

                        self.verify_data(
                            actual_value=float(add_size),
                            expected_value=float(expected_lots_open),
                            op=CompareOp.EQ,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"跟单者手数：{add_size}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-开仓日志-开平仓明细-平仓后")
        def test_query_closetrader_detail(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                ticket_open = var_manager.get_variable("ticket_open")
                params = {
                    "_t": current_timestamp_seconds,
                    "pageNo": 1,
                    "pageSize": 20,
                    "self_master_ticket": ticket_open
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgreport/api/getColumnsAndData/1568899025974796289',
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
                slave_ticket_list = self.json_utils.extract(
                    response.json(),
                    "$.result.data.records[0].slave_ticket",
                    default=[],
                    multi_match=True
                )
                follow_account = var_manager.get_variable("follow_account")
                if not slave_ticket_list:
                    attach_body = f"跟单账号：{follow_account}，返回的slave_ticket列表为空（暂无数据）"
                else:
                    attach_body = f"跟单账号：{follow_account}，返回 {len(slave_ticket_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"跟单账号：{follow_account}结果",
                    attachment_type="text/plain"
                )

                for idx, slave_ticket in enumerate(slave_ticket_list):
                    order_no = var_manager.get_variable("order_no")
                    self.verify_data(
                        actual_value=slave_ticket,
                        expected_value=order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的订单号应为{slave_ticket}",
                        attachment_name=f"跟单账户:{follow_account}第 {idx + 1} 条记录校验"
                    )

                with allure.step("喊单者订单号校验"):
                    master_ticket = self.json_utils.extract(response.json(),
                                                            "$.result.data.records[0].master_ticket")
                    ticket_open = var_manager.get_variable("ticket_open")

                    self.verify_data(
                        actual_value=master_ticket,
                        expected_value=ticket_open,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"喊单者订单号符合预期",
                        attachment_name="喊单者订单号详情"
                    )
                    logger.info(f"喊单者订单号验证通过: {master_ticket}")

                with allure.step("喊单者手数校验"):
                    master_lots = self.json_utils.extract(response.json(),
                                                          "$.result.data.records[0].master_lots")
                    lots_open = var_manager.get_variable("lots_open")

                    self.verify_data(
                        actual_value=float(master_lots),
                        expected_value=float(lots_open),
                        op=CompareOp.EQ,
                        message=f"喊单者手数符合预期",
                        attachment_name="喊单者手数详情"
                    )
                    logger.info(f"喊单者手数验证通过: {master_lots}")

                with allure.step("跟单手数校验"):
                    slave_lots = self.json_utils.extract(response.json(),
                                                         "$.result.data.records[0].slave_lots")
                    if not slave_lots:
                        allure.attach("跟单手数为空", "跟单手数详情", allure.attachment_type.TEXT)
                    else:
                        lots_open = var_manager.get_variable("lots_open")
                        follow_periodP = var_manager.get_variable("follow_periodP")
                        trader_periodP = var_manager.get_variable("trader_periodP")
                        # 获取跟单净值比例
                        fixed_proportion = var_manager.get_variable("fixed_proportion")
                        # 百分比数据转换
                        follow_fixed_decimal = percentage_to_decimal(fixed_proportion)
                        expected_lots_open = lots_open * (follow_periodP / trader_periodP) * follow_fixed_decimal

                        # 最小手数限制（0.01）
                        min_order_size = 0.01
                        if expected_lots_open < min_order_size:
                            allure.attach(
                                f"计算预期手数{expected_lots_open} < 最小手数{min_order_size}，强制重置为{min_order_size}",
                                "预期手数调整说明", allure.attachment_type.TEXT)
                            expected_lots_open = min_order_size

                        self.verify_data(
                            actual_value=float(slave_lots),
                            expected_value=float(expected_lots_open),
                            op=CompareOp.EQ,
                            abs_tol=0.01,
                            message=f"跟单手数符合预期",
                            attachment_name="跟单手数详情"
                        )
                        logger.info(f"跟单手数验证通过: {slave_lots}")

                with allure.step("交易币种校验"):
                    master_symbol = self.json_utils.extract(response.json(),
                                                            "$.result.data.records[0].master_symbol")
                    symbol = var_manager.get_variable("symbol")

                    self.verify_data(
                        actual_value=master_symbol,
                        expected_value=symbol,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"交易币种符合预期",
                        attachment_name="交易币种详情"
                    )
                    logger.info(f"交易币种验证通过: {master_symbol}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库提取数据-平仓时间差")
        def test_dbquery_closeorder(self, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否新增成功"):
                ticket_open = var_manager.get_variable("ticket_open")

                # 优化后的数据库查询
                db_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM bchain_trader_subscribe_order WHERE master_ticket = %s",
                    (ticket_open,),
                )

                # 提取数据库中的值
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

            with allure.step("2. 提取数据库中的值"):
                slave_ticket = db_data[0]["slave_ticket"]
                print(f"输出：{slave_ticket}")
                logging.info(f"跟单账号订单号: {slave_ticket}")
                var_manager.set_runtime_variable("slave_ticket", slave_ticket)

                close_time_difference = db_data[0]["close_time_difference"]
                print(f"输出：{close_time_difference}")
                logging.info(f"平仓时间差（毫秒）: {close_time_difference}")
                var_manager.set_runtime_variable("close_time_difference", close_time_difference)
                allure.attach(f"平仓时间差（毫秒）: {close_time_difference}", "平仓时间差")

    @allure.story("场景4：跟随方式-按净值-100%-跟单方向反向")
    @allure.description("""
    ### 测试说明
    - 前置条件：有喊单账号、跟单账号，跟单已经和喊单有订阅关系
      1. 修改订阅信息，跟随方式-按净值-100%-跟单方向反向
      2. MT4进行登录，然后进行开仓，总手数0.01
      3. 账号管理-持仓订单-喊单和跟单数据校验
      4. 跟单管理-开仓日志-喊单和跟单数据校验
      5. 跟单管理-VPS管理-喊单和跟单数据校验
      6. MT4进行平仓
      7. 账号管理-历史订单-喊单和跟单数据校验
      8. 跟单管理-开仓日志-喊单和跟单数据校验
    - 预期结果：喊单和跟单数据校验正确
    """)
    # @pytest.mark.skipif(True, reason="跳过此用例")
    class Test_orderseng4(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-实时跟单-修改订阅数据")
        def test_query_updata_editPa(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_jeecg_rowkey = var_manager.get_variable("follow_jeecg_rowkey")
                data = {
                    "id": follow_jeecg_rowkey,
                    "direction": "REVERSE",
                    "followingMode": 4,
                    "fixedProportion": 100,
                    "fixedLots": None
                }
                response = self.send_put_request(
                    logged_session,
                    '/blockchain/master-slave/editPa',
                    json_data=data
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-实时跟单-订阅列表数据")
        def test_query_getColumnsAndData(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_account = var_manager.get_variable("follow_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "account": follow_account,
                    "pageNo": "1",
                    "pageSize": "20",
                    "status": "NORMAL,AUDIT"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )
            with allure.step("3. 提取数据"):
                fixed_proportion = self.json_utils.extract(response.json(),
                                                           "$.result.data.records[0].fixed_proportion")
                var_manager.set_runtime_variable("fixed_proportion", fixed_proportion)

        @pytest.mark.retry(n=3, delay=10)
        @allure.title("跟单管理-VPS管理-提取喊单者净值")
        def test_query_get_traderquit(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_account = var_manager.get_variable("trader_account")
                vpsrunIpAddr = var_manager.get_variable("vpsrunIpAddr")
                params = {
                    "_t": current_timestamp_seconds,
                    "pageNo": "1",
                    "pageSize": "50",
                    "accountLike": trader_account,
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

            with allure.step(f"3. 提取净值数据"):
                trader_equity = self.json_utils.extract(response.json(), "$.records[0].equity")
                currency = self.json_utils.extract(response.json(), "$.records[0].currency")

                if currency == "USD":
                    trader_periodP = round(float(trader_equity) * 1.0, 2)
                elif currency == "JPY":
                    trader_periodP = round(float(trader_equity) * 0.00672, 2)
                elif currency == "AUD":
                    trader_periodP = round(float(trader_equity) * 0.6251, 2)
                elif currency == "USC":
                    trader_periodP = round(float(trader_equity) * 0.01, 2)
                else:
                    pytest.fail(f"不支持的币种：{currency}，请补充币种转换逻辑")

                logging.info(f"币种的转换详情,当前币种{currency}，转换前：{trader_equity},转换后：{trader_periodP}")
                allure.attach(f"当前币种{currency}，转换前：{trader_equity},转换后：{trader_periodP}",
                              "币种类型转换详情", allure.attachment_type.TEXT)
                var_manager.set_runtime_variable("trader_periodP", trader_periodP)

        @allure.title("跟单管理-VPS管理-提取跟单者净值")
        def test_query_get_followquit(self, var_manager, logged_session):
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

            with allure.step(f"3. 提取净值数据"):
                follow_equity = self.json_utils.extract(response.json(), "$.records[0].equity")
                currency = self.json_utils.extract(response.json(), "$.records[0].currency")

                if currency == "USD":
                    follow_periodP = round(float(follow_equity) * 1.0, 2)
                elif currency == "JPY":
                    follow_periodP = round(float(follow_equity) * 0.00672, 2)
                elif currency == "AUD":
                    follow_periodP = round(float(follow_equity) * 0.6251, 2)
                elif currency == "USC":
                    follow_periodP = round(float(follow_equity) * 0.01, 2)
                else:
                    pytest.fail(f"不支持的币种：{currency}，请补充币种转换逻辑")

                logging.info(f"币种的转换详情,当前币种{currency}，转换前：{follow_equity},转换后：{follow_periodP}")
                allure.attach(f"当前币种{currency}，转换前：{follow_equity},转换后：{follow_periodP}",
                              "币种类型转换详情", allure.attachment_type.TEXT)
                var_manager.set_runtime_variable("follow_periodP", follow_periodP)

        @allure.title("公共方法-校验前操作")
        def test_run_public(self, var_manager, logged_session):
            # 实例化类
            public_front = PublicUtils()

            # 按顺序调用
            # 登录获取 token
            public_front.test_login(var_manager)
            # 平仓喊单账号
            public_front.test_close_trader(var_manager)
            # 平仓跟单账号
            public_front.test_close_follow(var_manager)
            # 清理魔术号相关数据
            public_front.test_query_magic(var_manager, logged_session)
            # 清理账号ID相关数据
            public_front.test_query_follow_passid(var_manager, logged_session)
            # 登录MT4账号获取token
            public_front.test_mt4_login(var_manager)
            # MT4平台开仓操作
            public_front.test_mt4_open(var_manager)

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @pytest.mark.retry(n=3, delay=5)
        @allure.title("账号管理-持仓订单-喊单者账号ID查询-开仓后")
        def test_query_opentrader_passid(self, var_manager, logged_session):
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
                    '/online/cgform/api/getData/402883977b38c9ca017b38c9caff0000',
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
                    attach_body = f"账号ID查询[{trader_account}]，返回的trader_id列表为空（暂无数据）"
                else:
                    attach_body = f"账号ID查询[{trader_account}]，返回 {len(trader_id_list)} 条记录"

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
                            message=f"订单号数据正确",
                            attachment_name="订单号详情"
                        )
                        logger.info(f"订单号数据正确,开仓订单号：{ticket_open} 喊单者订单号：{order_no}")

                    with allure.step("喊单手数校验-MT4开仓手数和持仓订单手数"):
                        order_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                        logging.info(f"喊单者手数是: {order_size}")

                        lots_open = var_manager.get_variable("lots_open")

                        self.verify_data(
                            actual_value=float(order_size),
                            expected_value=float(lots_open),
                            op=CompareOp.EQ,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"喊单者手数：{order_size} MT4开仓手数：{lots_open}")

                    with allure.step("喊单的订单方向校验"):
                        type = self.json_utils.extract(response.json(), "$.result.records[0].type")
                        logging.info(f"喊单者方向是: {type}")

                        self.verify_data(
                            actual_value=float(type),
                            expected_value=float(0),
                            op=CompareOp.EQ,
                            message=f"喊单者方向符合预期",
                            attachment_name="喊单者方向详情"
                        )
                        logger.info(f"喊单者方向：{type}")
                        allure.attach("0:buy  1:sell", "方向解释", allure.attachment_type.TEXT)

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库提取数据-提取跟单订单号")
        def test_dbquery_openorder(self, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否新增成功"):
                ticket_open = var_manager.get_variable("ticket_open")

                # 优化后的数据库查询
                db_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM bchain_trader_subscribe_order WHERE master_ticket = %s",
                    (ticket_open,),
                )

                # 提取数据库中的值
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

            with allure.step("2. 提取数据库中的值"):
                slave_ticket = db_data[0]["slave_ticket"]
                print(f"输出：{slave_ticket}")
                logging.info(f"跟单账号订单号: {slave_ticket}")
                var_manager.set_runtime_variable("slave_ticket", slave_ticket)

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("账号管理-持仓订单-跟单账号ID查询-开仓后")
        def test_query_openfollow_passid(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_pass_id = var_manager.get_variable("follow_pass_id")
                follow_account = var_manager.get_variable("follow_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "trader_id": follow_pass_id,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 20,
                    "superQueryMatchType": "and"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/402883977b38c9ca017b38c9caff0000',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 提取数据"):
                order_no = self.json_utils.extract(response.json(), "$.result.records[0].order_no")
                var_manager.set_runtime_variable("order_no", order_no)
                allure.attach(f"{order_no}", "跟单订单号", allure.attachment_type.TEXT)

            with allure.step(f"3. 查询校验"):
                trader_id_list = self.json_utils.extract(
                    response.json(),
                    "$.result.records[0].trader_id",
                    default=[],
                    multi_match=True
                )

                if not trader_id_list:
                    attach_body = f"账号ID查询[{follow_account}]，返回的trader_id列表为空（暂无数据）"
                else:
                    attach_body = f"账号ID查询[{follow_account}]，返回 {len(trader_id_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"账号ID:{follow_account}查询结果",
                    attachment_type="text/plain"
                )

                for idx, trader_id in enumerate(trader_id_list):
                    self.verify_data(
                        actual_value=int(trader_id),
                        expected_value=int(follow_pass_id),
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的账号ID应为{trader_id}",
                        attachment_name=f"账号ID:{follow_pass_id}第 {idx + 1} 条记录校验"
                    )

                with allure.step("喊单者订单号校验"):
                    master_order_no = self.json_utils.extract(response.json(), "$.result.records[0].master_order_no")
                    ticket_open = var_manager.get_variable("ticket_open")

                    self.verify_data(
                        actual_value=ticket_open,
                        expected_value=master_order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"订单号数据正确",
                        attachment_name="订单号详情"
                    )
                    logger.info(f"订单号数据正确,开仓订单号：{ticket_open} 喊单者订单号：{master_order_no}")

                with allure.step("跟单订单号校验"):
                    slave_ticket = var_manager.get_variable("slave_ticket")
                    self.verify_data(
                        actual_value=slave_ticket,
                        expected_value=order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"订单号数据正确",
                        attachment_name="订单号详情"
                    )
                    logger.info(f"订单号数据正确,跟单者订单号：{order_no} 数据库数据：{slave_ticket}")

                with allure.step("跟单手数校验"):
                    add_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                    if not add_size:
                        allure.attach("订单手数数据为空", "订单手数数据", allure.attachment_type.TEXT)
                    else:
                        lots_open = var_manager.get_variable("lots_open")
                        follow_periodP = var_manager.get_variable("follow_periodP")
                        trader_periodP = var_manager.get_variable("trader_periodP")
                        # 获取跟单净值比例
                        fixed_proportion = var_manager.get_variable("fixed_proportion")
                        # 百分比数据转换
                        follow_fixed_decimal = percentage_to_decimal(fixed_proportion)
                        expected_lots_open = lots_open * (follow_periodP / trader_periodP) * follow_fixed_decimal

                        # 最小手数限制（0.01）
                        min_order_size = 0.01
                        if expected_lots_open < min_order_size:
                            allure.attach(
                                f"计算预期手数{expected_lots_open} < 最小手数{min_order_size}，强制重置为{min_order_size}",
                                "预期手数调整说明", allure.attachment_type.TEXT)
                            expected_lots_open = min_order_size

                        self.verify_data(
                            actual_value=float(add_size),
                            expected_value=float(expected_lots_open),
                            op=CompareOp.EQ,
                            abs_tol=0.01,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"跟单者手数：{add_size}")

                with allure.step("跟单的订单方向校验"):
                    type = self.json_utils.extract(response.json(), "$.result.records[0].type")
                    logging.info(f"跟单方向是: {type}")

                    self.verify_data(
                        actual_value=float(type),
                        expected_value=float(1),
                        op=CompareOp.EQ,
                        message=f"跟单方向符合预期",
                        attachment_name="跟单方向详情"
                    )
                    logger.info(f"跟单方向：{type}")
                    allure.attach("0:buy  1:sell", "方向解释", allure.attachment_type.TEXT)

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-开仓日志-喊单账户查询-开仓后")
        def test_query_opentrader_getdata(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_account = var_manager.get_variable("trader_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "master_account": trader_account,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 20,
                    "superQueryMatchType": "and"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/2c934301834efb6801834efbe1ba0002',
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
                master_ticket_list = self.json_utils.extract(
                    response.json(),
                    "$.result.records[0].master_ticket",
                    default=[],
                    multi_match=True
                )

                if not master_ticket_list:
                    attach_body = f"喊单账户查询[{trader_account}]，返回的master_ticket列表为空（暂无数据）"
                else:
                    attach_body = f"喊单账户查询[{trader_account}]，返回 {len(master_ticket_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"喊单账户:{trader_account}查询结果",
                    attachment_type="text/plain"
                )

                for idx, master_ticket in enumerate(master_ticket_list):
                    ticket_open = var_manager.get_variable("ticket_open")
                    self.verify_data(
                        actual_value=master_ticket,
                        expected_value=ticket_open,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的订单号应为{master_ticket}",
                        attachment_name=f"喊单账户:{trader_account}第 {idx + 1} 条记录校验"
                    )

                with allure.step("喊单者手数校验"):
                    master_lots = self.json_utils.extract(response.json(),
                                                          "$.result.records[0].master_lots")
                    lots_open = var_manager.get_variable("lots_open")

                    self.verify_data(
                        actual_value=float(master_lots),
                        expected_value=float(lots_open),
                        op=CompareOp.EQ,
                        message=f"喊单者手数符合预期",
                        attachment_name="喊单者手数详情"
                    )
                    logger.info(f"喊单者手数验证通过: {lots_open}")

                with allure.step("交易币种校验"):
                    master_symbol = self.json_utils.extract(response.json(),
                                                            "$.result.records[0].master_symbol")
                    symbol = var_manager.get_variable("symbol")

                    self.verify_data(
                        actual_value=master_symbol,
                        expected_value=symbol,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"交易币种符合预期",
                        attachment_name="交易币种详情"
                    )
                    logger.info(f"交易币种验证通过: {master_symbol}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-开仓日志-开平仓明细-开仓后")
        def test_query_opentrader_detail(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                ticket_open = var_manager.get_variable("ticket_open")
                params = {
                    "_t": current_timestamp_seconds,
                    "pageNo": 1,
                    "pageSize": 20,
                    "self_master_ticket": ticket_open
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgreport/api/getColumnsAndData/1568899025974796289',
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
                slave_ticket_list = self.json_utils.extract(
                    response.json(),
                    "$.result.data.records[0].slave_ticket",
                    default=[],
                    multi_match=True
                )
                follow_account = var_manager.get_variable("follow_account")
                if not slave_ticket_list:
                    attach_body = f"跟单账号：{follow_account}，返回的slave_ticket列表为空（暂无数据）"
                else:
                    attach_body = f"跟单账号：{follow_account}，返回 {len(slave_ticket_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"跟单账号：{follow_account}结果",
                    attachment_type="text/plain"
                )

                for idx, slave_ticket in enumerate(slave_ticket_list):
                    order_no = var_manager.get_variable("order_no")
                    self.verify_data(
                        actual_value=slave_ticket,
                        expected_value=order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的订单号应为{slave_ticket}",
                        attachment_name=f"跟单账户:{follow_account}第 {idx + 1} 条记录校验"
                    )

                with allure.step("喊单者订单号校验"):
                    master_ticket = self.json_utils.extract(response.json(),
                                                            "$.result.data.records[0].master_ticket")
                    ticket_open = var_manager.get_variable("ticket_open")

                    self.verify_data(
                        actual_value=master_ticket,
                        expected_value=ticket_open,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"喊单者订单号符合预期",
                        attachment_name="喊单者订单号详情"
                    )
                    logger.info(f"喊单者订单号验证通过: {master_ticket}")

                with allure.step("喊单者手数校验"):
                    master_lots = self.json_utils.extract(response.json(),
                                                          "$.result.data.records[0].master_lots")
                    lots_open = var_manager.get_variable("lots_open")

                    self.verify_data(
                        actual_value=float(master_lots),
                        expected_value=float(lots_open),
                        op=CompareOp.EQ,
                        message=f"喊单者手数符合预期",
                        attachment_name="喊单者手数详情"
                    )
                    logger.info(f"喊单者手数验证通过: {master_lots}")

                with allure.step("跟单手数校验"):
                    slave_lots = self.json_utils.extract(response.json(),
                                                         "$.result.data.records[0].slave_lots")
                    if not slave_lots:
                        allure.attach("跟单手数返回为空", "跟单手数详情", allure.attachment_type.TEXT)
                    else:
                        lots_open = var_manager.get_variable("lots_open")
                        follow_periodP = var_manager.get_variable("follow_periodP")
                        trader_periodP = var_manager.get_variable("trader_periodP")
                        # 获取跟单净值比例
                        fixed_proportion = var_manager.get_variable("fixed_proportion")
                        # 百分比数据转换
                        follow_fixed_decimal = percentage_to_decimal(fixed_proportion)
                        expected_lots_open = lots_open * (follow_periodP / trader_periodP) * follow_fixed_decimal

                        # 最小手数限制（0.01）
                        min_order_size = 0.01
                        if expected_lots_open < min_order_size:
                            allure.attach(
                                f"计算预期手数{expected_lots_open} < 最小手数{min_order_size}，强制重置为{min_order_size}",
                                "预期手数调整说明", allure.attachment_type.TEXT)
                            expected_lots_open = min_order_size

                        self.verify_data(
                            actual_value=float(slave_lots),
                            expected_value=float(expected_lots_open),
                            op=CompareOp.EQ,
                            abs_tol=0.01,
                            message=f"跟单手数符合预期",
                            attachment_name="跟单手数详情"
                        )
                        logger.info(f"跟单手数验证通过: {slave_lots}")

                with allure.step("交易币种校验"):
                    master_symbol = self.json_utils.extract(response.json(),
                                                            "$.result.data.records[0].master_symbol")
                    symbol = var_manager.get_variable("symbol")

                    self.verify_data(
                        actual_value=master_symbol,
                        expected_value=symbol,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"交易币种符合预期",
                        attachment_name="交易币种详情"
                    )
                    logger.info(f"交易币种验证通过: {master_symbol}")

                # @pytest.mark.skipif(True, reason="跳过此用例")

        @pytest.mark.retry(n=3, delay=10)
        @allure.title("跟单管理-VPS管理-喊单者账号-开仓后")
        def test_query_opentrader_getRecordList(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_account = var_manager.get_variable("trader_account")
                vpsrunIpAddr = var_manager.get_variable("vpsrunIpAddr")
                params = {
                    "_t": current_timestamp_seconds,
                    "pageNo": "1",
                    "pageSize": "50",
                    "accountLike": trader_account,
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
                with allure.step("喊单者手数校验-MT4开仓手数和持仓订单手数"):
                    totalLots = self.json_utils.extract(response.json(), "$.records[0].totalLots")
                    logging.info(f"手数是: {totalLots}")

                    lots_open = var_manager.get_variable("lots_open")

                    self.verify_data(
                        actual_value=float(totalLots),
                        expected_value=float(lots_open),
                        op=CompareOp.EQ,
                        message=f"手数符合预期",
                        attachment_name="手数详情"
                    )
                    logger.info(f"喊单者手数：{totalLots} MT4开仓手数：{lots_open}")

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
                    if not totalLots:
                        allure.attach("跟单手数为空", "跟单手数详情", allure.attachment_type.TEXT)
                    else:
                        lots_open = var_manager.get_variable("lots_open")
                        follow_periodP = var_manager.get_variable("follow_periodP")
                        trader_periodP = var_manager.get_variable("trader_periodP")
                        # 获取跟单净值比例
                        fixed_proportion = var_manager.get_variable("fixed_proportion")
                        # 百分比数据转换
                        follow_fixed_decimal = percentage_to_decimal(fixed_proportion)
                        expected_lots_open = lots_open * (follow_periodP / trader_periodP) * follow_fixed_decimal

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
                            abs_tol=0.01,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"跟单者手数：{totalLots}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("MT4平台平仓操作")
        def test_mt4_close(self, var_manager, db_transaction):
            # 实例化类
            public_front = PublicUtils()

            # MT4平台平仓操作
            public_front.test_mt4_close(var_manager, db_transaction)

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
                            message=f"订单号数据正确",
                            attachment_name="订单号详情"
                        )
                        logger.info(f"订单号数据正确,开仓订单号：{ticket_open} 喊单者订单号：{order_no}")

                    with allure.step("喊单手数校验-MT4开仓手数和持仓订单手数"):
                        order_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                        logging.info(f"喊单者手数是: {order_size}")

                        lots_open = var_manager.get_variable("lots_open")
                        self.verify_data(
                            actual_value=float(order_size),
                            expected_value=float(lots_open),
                            op=CompareOp.EQ,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"喊单者手数：{order_size} MT4开仓手数：{lots_open}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("账号管理-历史订单-跟单MT4账户查询-平仓后")
        def test_query_follow_id(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_pass_id = var_manager.get_variable("follow_pass_id")
                follow_account = var_manager.get_variable("follow_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "trader_id": follow_pass_id,
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

            with allure.step("3. 提取数据"):
                order_no = self.json_utils.extract(response.json(), "$.result.records[0].order_no")
                var_manager.set_runtime_variable("order_no", order_no)
                allure.attach(f"{order_no}", "跟单订单号", allure.attachment_type.TEXT)

            with allure.step(f"3. 查询校验"):
                trader_id_list = self.json_utils.extract(
                    response.json(),
                    "$.result.records[0].trader_id",
                    default=[],
                    multi_match=True
                )

                if not trader_id_list:
                    attach_body = f"MT4账号查询[{follow_account}]，返回的trader_id列表为空（暂无数据）"
                else:
                    attach_body = f"MT4账号查询[{follow_account}]，返回 {len(trader_id_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"账号ID:{follow_account}查询结果",
                    attachment_type="text/plain"
                )

                for idx, trader_id in enumerate(trader_id_list):
                    self.verify_data(
                        actual_value=int(trader_id),
                        expected_value=int(follow_pass_id),
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的账号ID应为{trader_id}",
                        attachment_name=f"账号ID:{follow_pass_id}第 {idx + 1} 条记录校验"
                    )

                with allure.step("喊单者订单号校验"):
                    master_order_no = self.json_utils.extract(response.json(),
                                                              "$.result.records[0].master_order_no")
                    ticket_open = var_manager.get_variable("ticket_open")

                    self.verify_data(
                        actual_value=ticket_open,
                        expected_value=master_order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"订单号数据正确",
                        attachment_name="订单号详情"
                    )
                    logger.info(f"订单号数据正确,开仓订单号：{ticket_open} 喊单者订单号：{master_order_no}")

                with allure.step("跟单订单号校验"):
                    slave_ticket = var_manager.get_variable("slave_ticket")
                    self.verify_data(
                        actual_value=slave_ticket,
                        expected_value=order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"订单号数据正确",
                        attachment_name="订单号详情"
                    )
                    logger.info(f"订单号数据正确,跟单者订单号：{order_no} 数据库数据：{slave_ticket}")

                with allure.step("跟单手数校验"):
                    add_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                    if not add_size:
                        allure.attach("订单手数数据为空", "订单手数数据", allure.attachment_type.TEXT)
                    else:
                        lots_open = var_manager.get_variable("lots_open")
                        follow_periodP = var_manager.get_variable("follow_periodP")
                        trader_periodP = var_manager.get_variable("trader_periodP")
                        # 获取跟单净值比例
                        fixed_proportion = var_manager.get_variable("fixed_proportion")
                        # 百分比数据转换
                        follow_fixed_decimal = percentage_to_decimal(fixed_proportion)
                        expected_lots_open = lots_open * (follow_periodP / trader_periodP) * follow_fixed_decimal
                        # 四舍五入保留两位小数
                        expected_lots_open = round(expected_lots_open, 2)

                        # 最小手数限制（0.01）
                        min_order_size = 0.01
                        if expected_lots_open < min_order_size:
                            allure.attach(
                                f"计算预期手数{expected_lots_open} < 最小手数{min_order_size}，强制重置为{min_order_size}",
                                "预期手数调整说明", allure.attachment_type.TEXT)
                            expected_lots_open = min_order_size

                        self.verify_data(
                            actual_value=float(add_size),
                            expected_value=float(expected_lots_open),
                            op=CompareOp.EQ,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"跟单者手数：{add_size}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-开仓日志-开平仓明细-平仓后")
        def test_query_closetrader_detail(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                ticket_open = var_manager.get_variable("ticket_open")
                params = {
                    "_t": current_timestamp_seconds,
                    "pageNo": 1,
                    "pageSize": 20,
                    "self_master_ticket": ticket_open
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgreport/api/getColumnsAndData/1568899025974796289',
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
                slave_ticket_list = self.json_utils.extract(
                    response.json(),
                    "$.result.data.records[0].slave_ticket",
                    default=[],
                    multi_match=True
                )
                follow_account = var_manager.get_variable("follow_account")
                if not slave_ticket_list:
                    attach_body = f"跟单账号：{follow_account}，返回的slave_ticket列表为空（暂无数据）"
                else:
                    attach_body = f"跟单账号：{follow_account}，返回 {len(slave_ticket_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"跟单账号：{follow_account}结果",
                    attachment_type="text/plain"
                )

                for idx, slave_ticket in enumerate(slave_ticket_list):
                    order_no = var_manager.get_variable("order_no")
                    self.verify_data(
                        actual_value=slave_ticket,
                        expected_value=order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的订单号应为{slave_ticket}",
                        attachment_name=f"跟单账户:{follow_account}第 {idx + 1} 条记录校验"
                    )

                with allure.step("喊单者订单号校验"):
                    master_ticket = self.json_utils.extract(response.json(),
                                                            "$.result.data.records[0].master_ticket")
                    ticket_open = var_manager.get_variable("ticket_open")

                    self.verify_data(
                        actual_value=master_ticket,
                        expected_value=ticket_open,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"喊单者订单号符合预期",
                        attachment_name="喊单者订单号详情"
                    )
                    logger.info(f"喊单者订单号验证通过: {master_ticket}")

                with allure.step("喊单者手数校验"):
                    master_lots = self.json_utils.extract(response.json(),
                                                          "$.result.data.records[0].master_lots")
                    lots_open = var_manager.get_variable("lots_open")

                    self.verify_data(
                        actual_value=float(master_lots),
                        expected_value=float(lots_open),
                        op=CompareOp.EQ,
                        message=f"喊单者手数符合预期",
                        attachment_name="喊单者手数详情"
                    )
                    logger.info(f"喊单者手数验证通过: {master_lots}")

                with allure.step("跟单手数校验"):
                    slave_lots = self.json_utils.extract(response.json(),
                                                         "$.result.data.records[0].slave_lots")
                    if not slave_lots:
                        allure.attach("跟单手数为空", "跟单手数详情", allure.attachment_type.TEXT)
                    else:
                        lots_open = var_manager.get_variable("lots_open")
                        follow_periodP = var_manager.get_variable("follow_periodP")
                        trader_periodP = var_manager.get_variable("trader_periodP")
                        # 获取跟单净值比例
                        fixed_proportion = var_manager.get_variable("fixed_proportion")
                        # 百分比数据转换
                        follow_fixed_decimal = percentage_to_decimal(fixed_proportion)
                        expected_lots_open = lots_open * (follow_periodP / trader_periodP) * follow_fixed_decimal

                        # 最小手数限制（0.01）
                        min_order_size = 0.01
                        if expected_lots_open < min_order_size:
                            allure.attach(
                                f"计算预期手数{expected_lots_open} < 最小手数{min_order_size}，强制重置为{min_order_size}",
                                "预期手数调整说明", allure.attachment_type.TEXT)
                            expected_lots_open = min_order_size

                        self.verify_data(
                            actual_value=float(slave_lots),
                            expected_value=float(expected_lots_open),
                            op=CompareOp.EQ,
                            abs_tol=0.01,
                            message=f"跟单手数符合预期",
                            attachment_name="跟单手数详情"
                        )
                        logger.info(f"跟单手数验证通过: {slave_lots}")

                with allure.step("交易币种校验"):
                    master_symbol = self.json_utils.extract(response.json(),
                                                            "$.result.data.records[0].master_symbol")
                    symbol = var_manager.get_variable("symbol")

                    self.verify_data(
                        actual_value=master_symbol,
                        expected_value=symbol,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"交易币种符合预期",
                        attachment_name="交易币种详情"
                    )
                    logger.info(f"交易币种验证通过: {master_symbol}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库提取数据-平仓时间差")
        def test_dbquery_closeorder(self, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否新增成功"):
                ticket_open = var_manager.get_variable("ticket_open")

                # 优化后的数据库查询
                db_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM bchain_trader_subscribe_order WHERE master_ticket = %s",
                    (ticket_open,),
                )

                # 提取数据库中的值
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

            with allure.step("2. 提取数据库中的值"):
                slave_ticket = db_data[0]["slave_ticket"]
                print(f"输出：{slave_ticket}")
                logging.info(f"跟单账号订单号: {slave_ticket}")
                var_manager.set_runtime_variable("slave_ticket", slave_ticket)

                close_time_difference = db_data[0]["close_time_difference"]
                print(f"输出：{close_time_difference}")
                logging.info(f"平仓时间差（毫秒）: {close_time_difference}")
                var_manager.set_runtime_variable("close_time_difference", close_time_difference)
                allure.attach(f"平仓时间差（毫秒）: {close_time_difference}", "平仓时间差")
