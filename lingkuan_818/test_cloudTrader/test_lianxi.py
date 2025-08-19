import allure
import logging
import pytest
import time
import math
from lingkuan_818.VAR.VAR import *
from lingkuan_818.conftest import var_manager
from lingkuan_818.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"


# @pytest.mark.skipif(condition=True, reason=SKIP_REASON)
@allure.feature("云策略下单功能测试")
@allure.description("""
### 测试说明
- 前置条件：有云策略和云跟单
  1. 修改跟单账号-跟单方向-反向
  2. 进行开仓，手数范围0.1-1，总订单3，总手数1
  3. 平仓-订单方向-sell，平仓成功
  4. 校验订单数据是否正确
- 预期结果：平仓的订单方向功能正确
""")
class TestMasOrderSend1(APITestBase):
    @allure.title("云策略-修改云跟单账号-跟单方向-反向")
    def test_copy_place_order(self, logged_session, var_manager):
        with allure.step("1.发送修改云跟单请求"):
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
            cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
            cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")

            request_data = [
                {
                    "traderList": [
                        cloudTrader_traderList_4
                    ],
                    "cloudId": cloudMaster_id,
                    "masterId": cloudTrader_traderList_2,
                    "masterAccount": cloudTrader_user_accounts_2,
                    "followDirection": 1,
                    "followMode": 1,
                    "followParam": 1,
                    "remainder": 0,
                    "placedType": 0,
                    "templateId": 1,
                    "followStatus": 1,
                    "followOpen": 1,
                    "followClose": 1,
                    "fixedComment": "ceshi",
                    "commentType": None,
                    "digits": 0,
                    "followTraderIds": [],
                    "sort": 100,
                    "remark": "",
                    "cfd": None,
                    "forex": None
                }
            ]

            response = self.send_post_request(
                logged_session,
                '/mascontrol/cloudTrader/cloudBatchUpdate',
                json_data=request_data
            )

        with allure.step("验证复制下单响应结果"):
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "复制下单响应msg字段应为success"
            )

        with allure.step("验证复制下单响应结果"):
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "复制下单响应msg字段应为success"
            )

    @allure.story("复制下单场景")
    @allure.title("云策略-复制下单操作")
    def test_copy_place_order(self, logged_session, var_manager):
        """执行云策略复制下单操作并验证请求结果"""
        with allure.step("发送复制下单请求"):
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")

            request_data = {
                "id": cloudMaster_id,
                "type": 0,
                "tradeType": 1,
                "intervalTime": 100,
                "cloudTraderId": [cloudTrader_traderList_4],
                "symbol": "XAUUSD",
                "placedType": 0,
                "startSize": "0.10",
                "endSize": "1.00",
                "totalNum": "3",
                "totalSzie": "1.00",
                "remark": "测试数据"
            }

            response = self.send_post_request(
                logged_session,
                '/mascontrol/cloudTrader/cloudOrderSend',
                json_data=request_data
            )

        with allure.step("验证复制下单响应结果"):
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "复制下单响应msg字段应为success"
            )

    @allure.story("复制下单场景")
    @allure.title("数据库校验-复制下单数据")
    def test_copy_verify_db(self, var_manager, db_transaction):
        """验证复制下单后数据库中的订单数据正确性"""
        with allure.step("查询复制订单详情数据"):
            cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
            sql = """
                   SELECT 
                       fod.size,
                       fod.send_no,
                       fod.magical,
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
               """
            params = ('0', cloudTrader_user_accounts_4)

            # 轮询等待数据库记录
            db_data = self.wait_for_database_record_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.open_time"
            )

        with allure.step("执行复制下单数据校验"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            if not db_data:
                pytest.fail("数据库查询结果为空，无法进行复制下单校验")

            # 订单状态校验
            status = db_data[0]["status"]
            assert status in (0, 1), \
                f"订单状态应为0(处理中)或1(全部成功)，实际为: {status}"
            logger.info(f"复制订单状态校验通过: {status}")

            # 结束手数校验
            min_lot_size = db_data[0]["min_lot_size"]
            endsize = trader_ordersend["endSize"]
            assert math.isclose(float(endsize), float(min_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
                f'结束手数不匹配，预期: {endsize}, 实际: {min_lot_size}'
            logger.info(f"复制下单结束手数校验通过: {endsize}")

            # 开始手数校验
            max_lot_size = db_data[0]["max_lot_size"]
            startSize = trader_ordersend["startSize"]
            assert math.isclose(float(startSize), float(max_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
                f'开始手数不匹配，预期: {startSize}, 实际: {max_lot_size}'
            logger.info(f"复制下单开始手数校验通过: {startSize}")

            # 总订单数量校验
            total_orders = db_data[0]["total_orders"]
            totalNum = trader_ordersend["totalNum"]
            assert math.isclose(float(totalNum), float(total_orders), rel_tol=1e-9, abs_tol=1e-9), \
                f'总订单数量不匹配，预期: {totalNum}, 实际: {total_orders}'
            logger.info(f"总订单数量校验通过: {totalNum}")

            # 总手数与指令表校验
            total_lots = db_data[0]["total_lots"]
            totalSzie = trader_ordersend["totalSzie"]
            assert math.isclose(float(totalSzie), float(total_lots), rel_tol=1e-9, abs_tol=1e-9), \
                f'总手数不匹配，预期: {totalSzie}, 实际: {total_lots}'
            logger.info(f"复制下单总手数与指令表校验通过: {totalSzie}")

            # 总手数与订单详情校验
            size_sum = sum(record["size"] for record in db_data)
            assert math.isclose(float(totalSzie), float(size_sum), rel_tol=1e-9, abs_tol=1e-9), \
                f'总手数与订单详情不匹配，预期: {totalSzie}, 实际: {size_sum}'
            logger.info(f"复制下单总手数与订单详情校验通过: {totalSzie}")

    @allure.story("复制下单场景")
    @allure.title("云策略-复制下单平仓操作")
    def test_copy_close_order(self, logged_session, var_manager):
        """执行复制下单的平仓操作并验证结果"""
        with allure.step("发送复制下单平仓请求"):
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
            new_user = var_manager.get_variable("new_user")

            request_data = {
                "id": cloudMaster_id,
                "flag": 0,
                "intervalTime": 0,
                "closeType": 0,
                "remark": "",
                "cloudTraderId": [cloudTrader_traderList_4],
                "symbol": new_user['symbol'],
                "type": 1
            }

            response = self.send_post_request(
                logged_session,
                '/mascontrol/cloudTrader/cloudOrderClose',
                json_data=request_data
            )

        with allure.step("验证复制平仓响应结果"):
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "复制平仓响应msg字段应为success"
            )

    @allure.story("复制下单场景")
    @allure.title("数据库校验-复制下单平仓数据")
    def test_copy_verify_close_db(self, var_manager, db_transaction):
        """验证复制下单平仓后数据库中的订单数据正确性"""
        with allure.step("查询复制平仓订单数据"):
            cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
            cloudTrader_vps_ids_3 = var_manager.get_variable("cloudTrader_vps_ids_3")

            sql = """
                   SELECT 
                       fod.size,
                       fod.close_no,
                       fod.magical,
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
                       foi.master_order,
                       foi.total_orders
                   FROM 
                       follow_order_detail fod
                   INNER JOIN 
                       follow_order_instruct foi 
                   ON 
                       foi.order_no = fod.close_no COLLATE utf8mb4_0900_ai_ci
                   WHERE foi.operation_type = %s
                       AND fod.account = %s
                       AND fod.trader_id = %s
               """
            params = ('1', cloudTrader_user_accounts_4, cloudTrader_vps_ids_3)

            # 轮询等待数据库记录
            db_data = self.wait_for_database_record_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.close_time"
            )

        with allure.step("执行复制平仓数据校验"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            if not db_data:
                pytest.fail("数据库查询结果为空，无法进行复制平仓校验")

            # 平仓状态校验
            status = db_data[0]["status"]
            assert status in (0, 1), \
                f"平仓状态应为0(处理中)或1(全部成功)，实际为: {status}"
            logger.info(f"复制平仓状态校验通过: {status}")

            # 平仓总手数校验
            totalSzie = trader_ordersend["totalSzie"]
            size_sum = sum(record["size"] for record in db_data)
            assert math.isclose(float(totalSzie), float(size_sum), rel_tol=1e-9, abs_tol=1e-9), \
                f'复制平仓总手数不匹配，预期: {totalSzie}, 实际: {size_sum}'
            logger.info(f"复制平仓总手数校验通过: {totalSzie}")

        time.sleep(25)
