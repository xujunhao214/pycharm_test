import time
from template_model.commons.api_base import APITestBase, logger
import allure
import logging
import json
import datetime
import re
import pytest
from template_model.VAR.VAR import *  # 确保包含vpsrunIpAddr、trader_pass_id、DATETIME_NOW等变量
from template_model.commons.jsonpath_utils import *
from template_model.commons.random_generator import *

# -------------------------- 多账号配置 --------------------------
FOLLOW_ACCOUNT_LIST = FOLLOW_ACCOUNT_LIST


@allure.story("绑定跟随者账号（多账号批量版）")
class Test_follow_batch(APITestBase):
    json_utils = JsonPathUtils()

    # -------------------------- 全局共用用例 --------------------------
    @allure.title("【全局】数据库查询-提取BrokerID")
    def test_dbbchain_trader(self, var_manager, db_transaction):
        with allure.step("1. 执行SQL查询bchain_trader_broker表"):
            sql = "SELECT id,name FROM bchain_trader_broker WHERE name = %s"
            params = ("CPT Markets",)
            db_data = self.query_database(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )
            assert db_data, f"未查询到Broker（name=CPT Markets），终止执行"

        with allure.step("2. 提取并存储全局BrokerID"):
            brokerId = db_data[0]["id"]
            var_manager.set_runtime_variable("follow_broker_id", brokerId)
            allure.attach(str(brokerId), name="全局BrokerID", attachment_type=allure.attachment_type.TEXT)
            logging.info(f"提取全局BrokerID成功：{brokerId}")

    @allure.title("【全局】提取用户ID")
    def test_user_list(self, var_manager, logged_session):
        login_config = var_manager.get_variable("login_config")
        target_email = login_config["username"]
        with allure.step("1. 发送用户列表GET请求"):
            params = {
                "_t": current_timestamp_seconds,
                "column": "createTime",
                "field": "id,,username,nickname,email,phone",
                "pageNo": "1",
                "pageSize": "20",
                "order": "desc"
            }
            response = self.send_get_request(
                logged_session,
                '/sys/user/list',
                params=params
            )

        with allure.step("2. 响应基础校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "用户列表接口success应为true"
            )

        with allure.step(f"3. 提取{target_email}的用户ID"):
            all_users = self.json_utils.extract(
                data=response.json(),
                expression="$.result.records[*]",
                multi_match=True,
                default=[]
            )
            assert all_users, "用户列表为空，接口返回异常"

            user_id = None
            for user in all_users:
                if user.get("email", "").lower() == target_email.lower():
                    user_id = user.get("id")
                    break

            assert user_id is not None, f"未找到email={target_email}的用户，请检查用户是否存在"
            var_manager.set_runtime_variable("follow_user_id", user_id)
            allure.attach(str(user_id), name="全局用户ID", attachment_type=allure.attachment_type.TEXT)
            logging.info(f"提取全局用户ID成功：{user_id}")

    @allure.title("【全局】提取服务器ID")
    def test_api_getData1(self, var_manager, logged_session):
        # target_server = "CPTMarkets-Demo"
        target_server = var_manager.get_variable("trader_master_server")
        follow_broker_id = var_manager.get_variable("follow_broker_id")
        assert follow_broker_id, "全局BrokerID未提取到，请先执行test_dbbchain_trader"

        with allure.step("1. 发送服务器列表GET请求"):
            params = {
                "_t": current_timestamp_seconds,
                "broker_id": follow_broker_id,
                "pageSize": "50"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/402883917b2f2594017b335d3ddb0001',
                params=params
            )

        with allure.step("2. 响应基础校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "服务器列表接口success应为true"
            )

        with allure.step(f"3. 提取{target_server}的服务器ID"):
            all_servers = self.json_utils.extract(
                data=response.json(),
                expression="$.result.records[*]",
                multi_match=True,
                default=[]
            )
            existing_servers = [s.get("server") for s in all_servers if s.get("server")]

            server_id = None
            for server in all_servers:
                if server.get("server") == target_server:
                    server_id = server.get("id")
                    break

            assert server_id is not None, f"未找到服务器[{target_server}]，当前列表：{existing_servers}"
            var_manager.set_runtime_variable("follow_server_id", server_id)
            allure.attach(str(server_id), name="全局服务器ID", attachment_type=allure.attachment_type.TEXT)
            logging.info(f"提取全局服务器ID成功：{server_id}")

    @allure.title("【全局】MT4绑定审核-提取计划ID（jeecg_row_key）")
    def test_api_getData7(self, var_manager, logged_session):
        with allure.step("1. 发送MT4审核计划GET请求"):
            params = {
                "_t": current_timestamp_seconds,
                "column": "name",
                "order": "asc"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/4028839781b865e40181b87163350007',
                params=params
            )

        with allure.step("2. 响应基础校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "MT4审核计划接口success应为true"
            )

        with allure.step("3. 提取jeecg_row_key（审核计划ID）"):
            jeecg_row_key = self.json_utils.extract(response.json(), "$.result.records[4].jeecg_row_key")
            assert jeecg_row_key is not None, "未提取到MT4审核计划ID（jeecg_row_key）"
            var_manager.set_runtime_variable("follow_jeecgrow_key", jeecg_row_key)
            allure.attach(str(jeecg_row_key), name="全局MT4审核计划ID", attachment_type=allure.attachment_type.TEXT)
            logging.info(f"提取全局MT4审核计划ID成功：{jeecg_row_key}")

    # -------------------------- 多账号专属完整流程 --------------------------
    @allure.title("【多账号】完整流程：绑定→审核→订阅")
    @pytest.mark.parametrize("follow_acc", FOLLOW_ACCOUNT_LIST)
    def test_follow_full_flow(self, follow_acc, var_manager, logged_session):
        """单个跟随者账号完整流程：绑定→提取审核ID→审核通过→清理历史订阅→订阅→校验结果"""
        # 提取当前账号信息并校验
        current_account = follow_acc.get("account")
        current_password = follow_acc.get("password")
        assert current_account, f"账号数据异常，缺少'account'字段：{follow_acc}"
        assert current_password, f"账号{current_account}缺少'password'字段"
        var_prefix = f"follow_{current_account}"
        allure.dynamic.description(f"当前执行账号：{current_account}")

        try:
            # 步骤1：绑定当前账号
            with allure.step(f"1. 绑定账号：{current_account}"):
                follow_user_id = var_manager.get_variable("follow_user_id")
                follow_broker_id = var_manager.get_variable("follow_broker_id")
                follow_server_id = var_manager.get_variable("follow_server_id")

                bind_data = {
                    "userId": follow_user_id,
                    "brokerId": follow_broker_id,
                    "serverId": follow_server_id,
                    "account": current_account,
                    "password": current_password,
                    "display": "PRIVATE",
                    "passwordType": "0",
                    "subscribeFee": "0",
                    "type": "SLAVE_REAL",
                    "platform": "4"
                }

                bind_response = self.send_post_request(
                    logged_session,
                    '/blockchain/account/bind',
                    json_data=bind_data
                )
                self.assert_json_value(
                    bind_response,
                    "$.success",
                    True,
                    f"账号{current_account}绑定失败"
                )
                allure.attach(
                    json.dumps(bind_data, indent=2, ensure_ascii=False),
                    name=f"{current_account}绑定请求数据",
                    attachment_type=allure.attachment_type.JSON
                )
                logging.info(f"账号{current_account}绑定成功")

            # 步骤2：提取当前账号MT4审核ID
            with allure.step(f"2. 提取{current_account}的MT4审核ID"):
                params = {
                    "_t": current_timestamp_seconds,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 20,
                    "superQueryMatchType": "and",
                    "status": "PENDING,VERIFICATION"
                }
                pass_response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/2c9a814a81d3a91b0181d3a91b250000',
                    params=params
                )

                self.assert_json_value(
                    pass_response,
                    "$.success",
                    True,
                    f"查询{current_account}MT4审核记录失败"
                )
                all_pass_records = self.json_utils.extract(
                    data=pass_response.json(),
                    expression="$.result.records[*]",
                    multi_match=True,
                    default=[]
                )
                existing_accounts = [r.get("account") for r in all_pass_records if r.get("account")]

                current_pass_id = None
                for record in all_pass_records:
                    if record.get("account") == current_account:
                        current_pass_id = record.get("id")
                        break

                assert current_pass_id is not None, (
                    f"未找到账号{current_account}的MT4审核ID！"
                    f"\n当前审核列表中的账号：{existing_accounts}"
                )
                var_manager.set_runtime_variable(f"{var_prefix}_pass_id", current_pass_id)
                allure.attach(
                    str(current_pass_id),
                    name=f"{current_account}MT4审核ID",
                    attachment_type=allure.attachment_type.TEXT
                )

            # 步骤3：MT4审核通过
            with allure.step(f"3. {current_account}的MT4审核通过"):
                follow_jeecgrow_key = var_manager.get_variable("follow_jeecgrow_key")
                vpsrunIpAddr = var_manager.get_variable("vpsrunIpAddr")
                current_pass_id = var_manager.get_variable(f"{var_prefix}_pass_id")

                pass_data = {
                    "pass": True,
                    "commission": False,
                    "planId": follow_jeecgrow_key,
                    "toSynDate": DATETIME_NOW,
                    "bindIpAddr": vpsrunIpAddr
                }

                audit_response = self.send_post_request(
                    logged_session,
                    f'/blockchain/account/pass/{current_pass_id}',
                    json_data=pass_data
                )
                self.assert_json_value(
                    audit_response,
                    "$.success",
                    True,
                    f"账号{current_account}MT4审核通过失败"
                )
                allure.attach(
                    json.dumps(pass_data, indent=2, ensure_ascii=False),
                    name=f"{current_account}审核请求数据",
                    attachment_type=allure.attachment_type.JSON
                )

            # 步骤4：清理历史订阅记录
            with allure.step(f"4. 清理{current_account}的历史订阅记录"):
                params = {
                    "_t": current_timestamp_seconds,
                    "account": current_account,
                    "pageNo": 1,
                    "pageSize": 100,
                    "status": "NORMAL,AUDIT"
                }
                clean_response = self.send_get_request(
                    logged_session,
                    '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                    params=params
                )

                self.assert_json_value(
                    clean_response,
                    "$.success",
                    True,
                    f"查询{current_account}历史订阅记录失败"
                )
                history_records = self.json_utils.extract(
                    data=clean_response.json(),
                    expression="$.result.data.records[*]",
                    multi_match=True,
                    default=[]
                )

                if history_records:
                    delete_count = 0
                    for record in history_records:
                        record_id = record.get("id")
                        if record_id:
                            delete_response = self.send_delete_request(
                                logged_session,
                                '/blockchain/master-slave/deletePa',
                                json_data={"id": record_id}
                            )
                            self.assert_json_value(
                                delete_response,
                                "$.success",
                                True,
                                f"删除{current_account}历史订阅记录（ID：{record_id}）失败"
                            )
                            delete_count += 1
                    allure.attach(f"成功删除{delete_count}条记录", name=f"{current_account}清理结果")
                else:
                    allure.attach("无历史记录", name=f"{current_account}清理结果")

            # 步骤5：订阅跟单
            with allure.step(f"5. 进行刷新"):
                with allure.step("1. 发送请求"):
                    params = {
                        "_t": current_timestamp_seconds,
                        "column": "id",
                        "order": "desc",
                        "pageNo": 1,
                        "pageSize": 20,
                        "status": "VERIFICATION,PASS,PENDING,ERROR",
                        "type": "SLAVE_REAL"
                    }
                    self.send_get_request(
                        logged_session,
                        '/online/cgform/api/getData/2c9a814a81d3a91b0181e04a36e00001',
                        params=params
                    )

            # 步骤6：订阅跟单
            with allure.step(f"6. {current_account}订阅跟单"):
                trader_pass_id = var_manager.get_variable("trader_pass_id")
                current_pass_id = var_manager.get_variable(f"{var_prefix}_pass_id")
                assert trader_pass_id, "主账号trader_pass_id未配置"

                subscribe_data = {
                    "masterId": trader_pass_id,
                    "slaveId": current_pass_id,
                    "direction": "FORWARD",
                    "followingMode": "2",
                    "fixedProportion": "100",
                    "fixedLots": None,
                    "order": {"paymentAccount": "", "paymentMethod": ""},
                }

                subscribe_response = self.send_post_request(
                    logged_session,
                    '/blockchain/master-slave/admin/add',
                    json_data=subscribe_data
                )
                self.assert_json_value(
                    subscribe_response,
                    "$.success",
                    True,
                    f"{current_account}订阅跟单失败"
                )
                allure.attach(
                    json.dumps(subscribe_data, indent=2),
                    name=f"{current_account}订阅数据",
                    attachment_type=allure.attachment_type.JSON
                )

            # 步骤7：校验订阅结果
            with allure.step(f"7. 校验{current_account}的订阅记录"):
                params = {
                    "_t": current_timestamp_seconds,
                    "account": current_account,
                    "pageNo": 1,
                    "pageSize": 100,
                    "status": "NORMAL,AUDIT"
                }
                verify_response = self.send_get_request(
                    logged_session,
                    '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                    params=params
                )

                self.assert_json_value(
                    verify_response,
                    "$.success",
                    True,
                    f"校验{current_account}订阅记录失败"
                )
                result = self.json_utils.extract(
                    verify_response.json(),
                    "$.result.data.records[*]",
                    multi_match=True,
                    default=[]
                )

                if not result:
                    pytest.fail(f"{current_account}未查询到订阅记录")
                else:
                    follow_jeecg_rowkey = self.json_utils.extract(
                        verify_response.json(),
                        "$.result.data.records[0].jeecg_row_key"
                    )
                    var_manager.set_runtime_variable(f"{var_prefix}_jeecg_rowkey", follow_jeecg_rowkey)
                    allure.attach("订阅记录存在", name=f"{current_account}订阅结果")
                    logging.info(f"账号{current_account}订阅校验成功")

        except Exception as e:
            error_msg = f"账号{current_account}执行失败：{str(e)[:200]}"
            allure.attach(error_msg, name=f"{current_account}失败详情",
                          attachment_type=allure.attachment_type.TEXT)
            logging.error(error_msg, exc_info=True)
            pytest.fail(error_msg)
