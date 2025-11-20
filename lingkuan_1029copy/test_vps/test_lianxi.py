import time
import math
import allure
import logging
import pytest
from lingkuan_1029copy.VAR.VAR import *
from lingkuan_1029copy.conftest import var_manager
from lingkuan_1029copy.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS策略下单-开仓的场景校验-buy")
class TestVPSOrdersendbuy(APITestBase):
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景6： VPS看板-跟单账号超过最大手数")
    @allure.description("""
        ### 测试说明
        - 前置条件：有vps策略和vps跟单
          1. 获取策略账号服务器最大手数
          2. VPS看板-策略账号进行开仓
          3. 跟单账号进行校验，超过最大手数
          4. 策略账号进行平仓
        - 预期结果：跟单账号开仓失败，超过最大手数
        """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSOrderSend6(APITestBase):
        @allure.title("数据库提取该服务器最大手数")
        def test_dbquery_maxlots(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 数据库的SQL查询"):
                new_user = var_manager.get_variable("new_user")
                sql = f""" SELECT * From follow_platform where server = %s """
                params = (new_user["platform"],)

                db_data = self.query_database(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
            with allure.step("2. 提取数据并保存"):
                max_lots = db_data[0]["max_lots"]
                if max_lots is None:
                    # 数据库查询为空，主动存入None，覆盖旧数据
                    var_manager.set_runtime_variable("max_lots", None)
                    logger.info(f"服务器{new_user['platform']}无最大手数数据，已保存空值")
                    allure.attach("None", f"服务器{new_user['platform']}的最大手数", allure.attachment_type.TEXT)
                else:
                    var_manager.set_runtime_variable("max_lots", max_lots)
                    logger.info(f"服务器{new_user['platform']}的最大手数是：{max_lots}")
                    allure.attach(str(max_lots), f"服务器{new_user['platform']}的最大手数", allure.attachment_type.TEXT)

            # 其他查询逻辑同理：查询为空时主动存空值
            with allure.step("3. 全局配置-数据库的SQL查询"):
                sql = f""" SELECT * From sys_params where param_name= %s """
                params = ("最大手数配置",)
                db_data = self.query_database(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
            with allure.step("4. 提取数据并保存"):
                param_value = db_data[0]["param_value"]
                if param_value is None:
                    var_manager.set_runtime_variable("param_value", None)  # 存空值覆盖旧数据
                    logger.info(f"全局配置无最大手数数据，已保存空值")
                    allure.attach("None", f"全局配置的最大手数", allure.attachment_type.TEXT)
                else:
                    var_manager.set_runtime_variable("param_value", param_value)
                    logger.info(f"全局配置的最大手数是：{param_value}")
                    allure.attach(str(param_value), f"全局配置的最大手数", allure.attachment_type.TEXT)

            with allure.step("5. 数据库的SQL查询"):
                addVPS_MT5Slave = var_manager.get_variable("addVPS_MT5Slave")
                sql = f""" SELECT * From follow_platform where server = %s """
                params = (addVPS_MT5Slave["platform"],)

                db_data = self.query_database(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
            with allure.step("6. 提取数据并保存"):
                MT5max_lots = db_data[0]["max_lots"]
                if MT5max_lots is None:
                    # 数据库查询为空，主动存入None，覆盖旧数据
                    var_manager.set_runtime_variable("MT5max_lots", None)
                    logger.info(f"服务器{addVPS_MT5Slave['platform']}无最大手数数据，已保存空值")
                    allure.attach("None", f"服务器{addVPS_MT5Slave['platform']}的最大手数", allure.attachment_type.TEXT)
                else:
                    var_manager.set_runtime_variable("MT5max_lots", MT5max_lots)
                    logger.info(f"服务器{addVPS_MT5Slave['platform']}的最大手数是：{MT5max_lots}")
                    allure.attach(str(MT5max_lots), f"服务器{addVPS_MT5Slave['platform']}的最大手数",
                                  allure.attachment_type.TEXT)

        @pytest.mark.url("vps")
        # @pytest.mark.skipif(True, reason=SKIP_REASON)
        @allure.title("跟单软件看板-VPS数据-策略开仓")
        def test_trader_orderSend(self, class_random_str, var_manager, logged_session):
            # 1. 发送策略开仓请求
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            max_lots = var_manager.get_variable("max_lots")
            param_value = var_manager.get_variable("param_value")
            MT5max_lots = var_manager.get_variable("MT5max_lots")

            if max_lots == None and MT5max_lots == None:
                skip_msg = "策略和跟单的服务器都没有最大手数限制，跳过执行"
                logging.info(skip_msg)
                pytest.skip(skip_msg)

            elif max_lots == None and MT5max_lots != None:
                max_lots = float(param_value)
                var_manager.set_runtime_variable("send_maxlots", max_lots)
                data = {
                    "symbol": trader_ordersend["symbol"],
                    "placedType": 0,
                    "remark": class_random_str,
                    "intervalTime": 100,
                    "type": 0,
                    "totalNum": "1",
                    "totalSzie": "",
                    "startSize": max_lots,
                    "endSize": max_lots,
                    "traderId": vps_trader_id
                }
                response = self.send_post_request(
                    logged_session,
                    '/subcontrol/trader/orderSend',
                    json_data=data,
                )

            elif max_lots != None and MT5max_lots != None and max_lots > MT5max_lots:
                max_lots = max_lots
                var_manager.set_runtime_variable("send_maxlots", max_lots)
                data = {
                    "symbol": trader_ordersend["symbol"],
                    "placedType": 0,
                    "remark": class_random_str,
                    "intervalTime": 100,
                    "type": 0,
                    "totalNum": "1",
                    "totalSzie": "",
                    "startSize": max_lots,
                    "endSize": max_lots,
                    "traderId": vps_trader_id
                }
                response = self.send_post_request(
                    logged_session,
                    '/subcontrol/trader/orderSend',
                    json_data=data,
                )

            # 2. 验证响应状态码和内容
            self.assert_response_status(
                response,
                200,
                "策略开仓失败"
            )
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        @allure.title("数据库校验-策略开仓-跟单指令及订单详情数据检查")
        def test_dbquery_orderSend(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                addVPS_MT5Slave = var_manager.get_variable("addVPS_MT5Slave")
                sql = f"""
                           SELECT
                               fod.size,
                               fod.comment,
                               fod.send_no,
                               fod.magical,
                               fod.open_price,
                               fod.remark,
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
                           WHERE fod.account = %s
                               AND fod.comment = %s
                               """
                params = (
                    addVPS_MT5Slave["account"],
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证备注信息"):
                    open_remark = db_data[0]["remark"]
                    self.verify_data(
                        actual_value=open_remark,
                        expected_value=("超过最大手数限制"),
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message="开仓失败信息符合预期",
                        attachment_name="失败信息详情"
                    )
                    logging.info(f"失败信息验证通过: {open_remark}")

                    send_maxlots = var_manager.get_variable("send_maxlots")
                    MT5max_lots = var_manager.get_variable("MT5max_lots")
                    param_value = var_manager.get_variable("param_value")
                    allure.attach(
                        f"服务器最大手数：{MT5max_lots}，全局限制最大手数：{param_value}，下单手数：{send_maxlots}",
                        "失败信息详情",
                        allure.attachment_type.TEXT
                    )

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略平仓")
        def test_trader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            new_user = var_manager.get_variable("new_user")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": vps_trader_id,
                "account": new_user["account"]
            }
            response = self.send_post_request(
                logged_session,
                '/subcontrol/trader/orderClose',
                json_data=data,
            )

            # 2. 验证响应
            self.assert_response_status(
                response,
                200,
                "平仓失败"
            )
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )
