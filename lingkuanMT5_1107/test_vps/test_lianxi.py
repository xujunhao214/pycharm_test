import time
import math
import allure
import logging
import pytest
from lingkuan_1107.VAR.VAR import *
from lingkuan_1107.conftest import var_manager
from lingkuan_1107.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS策略下单-开仓的场景校验-buy")
class TestVPSOrdersendbuy(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-新增MT5跟单账号")
    def test_create_addMT5Slave(self, var_manager, logged_session, encrypted_password):
        # 1. 发送新增策略账号请求
        cloudTrader_vps_id = var_manager.get_variable("cloudTrader_vps_id")
        add_MT5Slave = var_manager.get_variable("add_MT5Slave")
        data = {
            "traderId": cloudTrader_vps_id,
            "platform": add_MT5Slave["platform"],
            "account": add_MT5Slave["account"],
            "password": encrypted_password,
            "remark": "",
            "followDirection": 0,
            "followMode": 1,
            "remainder": 0,
            "followParam": 1,
            "placedType": 0,
            "templateId": 1,
            "followStatus": 1,
            "followOpen": 1,
            "followClose": 1,
            "followRep": 0,
            "fixedComment": "",
            "commentType": "",
            "digits": 0,
            "cfd": "",
            "forex": "",
            "abRemark": "",
            "platformType": 1,
            "followTraderSymbolEntityList": []
        }
        response = self.send_post_request(
            logged_session,
            '/subcontrol/follow/addSlave',
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "创建用户失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-新增跟单账号")
    def test_dbquery_addMT5slave(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            add_MT5Slave = var_manager.get_variable("add_MT5Slave")
            # 执行数据库查询
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_trader WHERE account = %s",
                (add_MT5Slave['account'],)
            )

            if not db_data:
                pytest.fail("数据库查询结果为空，订单可能没有入库")

            MT5vps_addslave_id = db_data[0]["id"]
            logging.info(f"新增跟单账号ID: {MT5vps_addslave_id}")
            var_manager.set_runtime_variable("MT5vps_addslave_id", MT5vps_addslave_id)

        with allure.step("2. 校验账号状态和净值"):
            status = db_data[0]["status"]
            assert status == 0, f"账号 {add_MT5Slave['account']} 状态异常：预期status=0，实际={status}"
            logging.info(f"账号 {add_MT5Slave['account']} 状态异常：预期status=0，实际={status}")

            euqit = db_data[0]["euqit"]
            assert euqit >= 0, f"账号 {add_MT5Slave['account']} 净值异常：预期euqit>=0，实际={euqit}"
            logging.info(f"账号 {add_MT5Slave['account']} 净值异常：预期euqit>=0，实际={euqit}")

            db_data2 = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s",
                (add_MT5Slave['account'],)
            )

            if not db_data2:
                pytest.fail("数据库查询结果为空，订单可能没有入库")

            slave_account = db_data2[0]["slave_account"]
            assert slave_account == add_MT5Slave[
                'account'], f"账号新增失败，新增账号：{add_MT5Slave['account']}  数据库账号:{slave_account}"
            logging.info(f"账号新增成功，新增账号：{add_MT5Slave['account']}  数据库账号:{slave_account}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略列表-新增MT5云跟单账号")
    def test_create_addMT5Trader(self, var_manager, logged_session, encrypted_password):
        # 1. 发送新增策略账号请求
        MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
        cloudMaster_id = var_manager.get_variable("cloudMaster_id")
        cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
        cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
        data = [
            {
                "traderList": [
                    MT5vps_addslave_id
                ],
                "cloudId": cloudMaster_id,
                "masterId": cloudTrader_traderList_2,
                "masterAccount": cloudTrader_user_accounts_2,
                "followDirection": 0,
                "followMode": 1,
                "followParam": 1,
                "remainder": 0,
                "placedType": 0,
                "templateId": 1,
                "followStatus": 1,
                "followOpen": 1,
                "followClose": 1,
                "fixedComment": "",
                "commentType": "",
                "digits": "",
                "followTraderIds": [],
                "sort": "",
                "remark": ""
            }
        ]
        response = self.send_post_request(
            logged_session,
            '/mascontrol/cloudTrader/cloudBatchAdd',
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "创建用户失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-新增MT5云跟单账号")
    def test_dbcloudTrader_MT5BatchAdd(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            add_MT5Slave = var_manager.get_variable("add_MT5Slave")
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")

            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_cloud_trader WHERE account = %s and cloud_id = %s",
                (add_MT5Slave["account"], cloudMaster_id,)
            )

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，新增跟单账号失败")

            cloudTrader_MT5traderID = db_data[0]['id']
            var_manager.set_runtime_variable("cloudTrader_MT5traderID", cloudTrader_MT5traderID)
            logging.info(f"新增云跟单账号id是：{cloudTrader_MT5traderID}")

        with allure.step("3. 提取用户数据"):
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_trader_user WHERE account = %s",
                (add_MT5Slave["account"],)
            )

            if not db_data:
                pytest.fail("数据库查询结果为空，新增跟单账号失败")

            cloudTrader_MT5userID = db_data[0]['id']
            var_manager.set_runtime_variable("cloudTrader_MT5userID", cloudTrader_MT5userID)
            logging.info(f"账号id是：{cloudTrader_MT5userID}")
