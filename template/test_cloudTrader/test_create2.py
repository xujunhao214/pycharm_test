import time
import json
import pytest
import allure
import logging
from template.commons.api_base import APITestBase
from template.VAR.VAR import *  # 确保包含DATETIME_NOW、current_timestamp_seconds等
from template.commons.jsonpath_utils import JsonPathUtils
from template.commons.random_generator import *

# -------------------------- 1. 多账号配置（支持动态增减） --------------------------
FOLLOW_ACCOUNT_LIST = [
    {"account": "301392106", "password": "0sgsgtu"},
    {"account": "301392107", "password": "joj6vwd"},
    {"account": "301392108", "password": "yw5piys3"},
    {"account": "301392109", "password": "an0emxc"},
]

# -------------------------- 2. 变量名常量定义（避免硬编码错误） --------------------------
# 全局变量名（所有账号共用）
GLOBAL_BROKER_ID = "global_follow_broker_id"
GLOBAL_USER_ID = "global_follow_user_id"
GLOBAL_SERVER_ID = "global_follow_server_id"
GLOBAL_JEECG_ROW_KEY = "global_follow_jeecgrow_key"
GLOBAL_TRADER_PASS_ID = "global_trader_pass_id"  # 主账号审核ID（假设全局存在）
GLOBAL_VPS_IP = "vpsrunIpAddr"  # VPS IP变量

# 账号专属变量名模板（{acc}为账号占位符）
FOLLOW_PASS_ID_TPL = "follow_{acc}_pass_id"  # 账号专属MT4审核ID
FOLLOW_SUBSCRIBE_ID_TPL = "follow_{acc}_subscribe_id"  # 账号专属订阅ID
FOLLOW_JEECG_ROWKEY_TPL = "follow_{acc}_jeecg_rowkey"  # 账号专属订阅记录ID


@allure.story("绑定跟随者账号（多账号批量版）")
class Test_follow_batch(APITestBase):
    json_utils = JsonPathUtils()

    # -------------------------- 3. 全局数据初始化（仅执行一次） --------------------------
    def setup_class(self):
        """校验账号列表格式，初始化批量执行环境"""
        for idx, acc_info in enumerate(FOLLOW_ACCOUNT_LIST):
            assert "account" in acc_info and acc_info["account"], f"第{idx + 1}个账号缺少'account'字段"
            assert "password" in acc_info and acc_info["password"], f"第{idx + 1}个账号缺少'password'字段"
        logging.info(f"多账号初始化完成，共{len(FOLLOW_ACCOUNT_LIST)}个账号待处理")

    @allure.title("全局-提取BrokerID（共用）")
    def test_extract_global_broker_id(self, var_manager, db_transaction):
        with allure.step("1. 执行SQL查询bchain_trader_broker表"):
            sql = "SELECT id,name FROM bchain_trader_broker WHERE name = %s"
            params = ("CPT Markets",)
            db_data = self.query_database(db_transaction=db_transaction, sql=sql, params=params)
            assert db_data, f"未查询到Broker（name={params[0]}），终止执行"

        with allure.step("2. 保存全局BrokerID到变量管理器"):
            global_broker_id = db_data[0]["id"]
            var_manager.set_runtime_variable(GLOBAL_BROKER_ID, global_broker_id)
            allure.attach(str(global_broker_id), name="全局BrokerID", attachment_type=allure.attachment_type.TEXT)
            logging.info(f"[全局变量] 保存 {GLOBAL_BROKER_ID} = {global_broker_id}")

    @allure.title("全局-提取用户ID和服务器ID（共用）")
    def test_extract_global_user_server_id(self, var_manager, logged_session):
        # 提取全局用户ID
        global_user_id = self._extract_user_id(logged_session, target_email="xujunhao@163.com")
        var_manager.set_runtime_variable(GLOBAL_USER_ID, global_user_id)
        logging.info(f"[全局变量] 保存 {GLOBAL_USER_ID} = {global_user_id}")

        # 提取全局服务器ID（依赖全局BrokerID）
        global_broker_id = var_manager.get_variable(GLOBAL_BROKER_ID)
        global_server_id = self._extract_server_id(logged_session, global_broker_id, target_server="CPTMarkets-Demo")
        var_manager.set_runtime_variable(GLOBAL_SERVER_ID, global_server_id)
        logging.info(f"[全局变量] 保存 {GLOBAL_SERVER_ID} = {global_server_id}")

        # 附加全局变量到报告
        allure.attach(f"用户ID：{global_user_id}\n服务器ID：{global_server_id}",
                      name="全局用户ID+服务器ID",
                      attachment_type=allure.attachment_type.TEXT)

    @allure.title("全局-提取MT4审核JeecgRowKey（共用）")
    def test_extract_global_jeecg_row_key(self, var_manager, logged_session):
        global_jeecg_row_key = self._extract_jeecg_row_key(logged_session)
        var_manager.set_runtime_variable(GLOBAL_JEECG_ROW_KEY, global_jeecg_row_key)
        allure.attach(str(global_jeecg_row_key), name="全局MT4审核JeecgRowKey",
                      attachment_type=allure.attachment_type.TEXT)
        logging.info(f"[全局变量] 保存 {GLOBAL_JEECG_ROW_KEY} = {global_jeecg_row_key}")

    # -------------------------- 4. 多账号批量执行核心用例 --------------------------
    @allure.title("批量绑定跟随者账号")
    @pytest.mark.parametrize("acc_info", FOLLOW_ACCOUNT_LIST)
    @pytest.mark.dependency(depends=[
        "test_extract_global_broker_id",
        "test_extract_global_user_server_id",
        "test_extract_global_jeecg_row_key"
    ])
    def test_batch_follow_account(self, acc_info, var_manager, logged_session):
        current_acc = acc_info["account"]  # 当前账号（唯一标识）
        current_pwd = acc_info["password"]

        # 动态标题+账号信息附加（Allure报告区分账号）
        allure.dynamic.title(f"绑定跟随者账号-{current_acc}")
        allure.attach(f"账号：{current_acc}\n密码：{current_pwd}",
                      name=f"账号{current_acc}基础信息",
                      attachment_type=allure.attachment_type.TEXT)

        try:
            # 步骤1：首次绑定账号（期望成功）
            self._bind_account(logged_session, var_manager, current_acc, current_pwd, expect_success=True)

            # 步骤2：重复绑定校验（期望失败，提示已绑定）
            self._bind_account(logged_session, var_manager, current_acc, current_pwd, expect_success=False)

            # 步骤3：提取当前账号的MT4审核ID（保存为账号专属变量）
            follow_pass_id = self._extract_mt4_audit_id(logged_session, var_manager, current_acc)
            follow_pass_id_key = FOLLOW_PASS_ID_TPL.format(acc=current_acc)  # 生成账号专属变量名
            var_manager.set_runtime_variable(follow_pass_id_key, follow_pass_id)
            allure.attach(str(follow_pass_id), name=f"账号{current_acc}MT4审核ID",
                          attachment_type=allure.attachment_type.TEXT)
            logging.info(f"[账号{current_acc}专属变量] 保存 {follow_pass_id_key} = {follow_pass_id}")

            # 步骤4：MT4审核通过（读取当前账号专属审核ID）
            self._pass_mt4_audit(logged_session, var_manager, current_acc)

            # 步骤5：清理当前账号的历史订阅记录
            self._clean_subscribe_record(logged_session, current_acc)

            # 步骤6：订阅跟单（保存账号专属订阅ID）
            subscribe_id = self._subscribe_follow(logged_session, var_manager, current_acc)
            follow_subscribe_id_key = FOLLOW_SUBSCRIBE_ID_TPL.format(acc=current_acc)
            var_manager.set_runtime_variable(follow_subscribe_id_key, subscribe_id)
            allure.attach(str(subscribe_id), name=f"账号{current_acc}订阅ID",
                          attachment_type=allure.attachment_type.TEXT)
            logging.info(f"[账号{current_acc}专属变量] 保存 {follow_subscribe_id_key} = {subscribe_id}")

            # 步骤7：校验订阅记录（期望存在）
            self._verify_subscribe_record(logged_session, var_manager, current_acc, expect_exist=True)

            logging.info(f"✅ 账号{current_acc}绑定流程全部完成")

        except Exception as e:
            error_msg = f"❌ 账号{current_acc}绑定失败：{str(e)[:200]}"
            allure.attach(error_msg, name=f"账号{current_acc}执行失败详情", attachment_type=allure.attachment_type.TEXT)
            logging.error(error_msg, exc_info=True)
            pytest.fail(error_msg)

    # -------------------------- 5. 封装复用方法（移除所有error_msg参数） --------------------------
    def _extract_user_id(self, logged_session, target_email):
        """提取全局用户ID（共用方法）"""
        with allure.step(f"提取用户ID（目标邮箱：{target_email}）"):
            params = {
                "_t": current_timestamp_seconds,
                "column": "createTime",
                "field": "id,,username,nickname,email,phone",
                "pageNo": "1",
                "pageSize": "20",
                "order": "desc"
            }
            response = self.send_get_request(logged_session, '/sys/user/list', params=params)

            # 修复：移除error_msg参数，通过assert信息提示
            self.assert_json_value(response, "$.success", True)
            all_users = self.json_utils.extract(response.json(), "$.result.records[*]", multi_match=True, default=[])
            assert all_users, "用户列表为空，无法提取用户ID"

            user_id = None
            for user in all_users:
                if user.get("email", "").lower() == target_email.lower():
                    user_id = user.get("id")
                    break
            assert user_id is not None, f"未找到邮箱={target_email}的用户"
            return user_id

    def _extract_server_id(self, logged_session, broker_id, target_server):
        """提取全局服务器ID（共用方法）"""
        with allure.step(f"提取服务器ID（BrokerID：{broker_id}，目标服务器：{target_server}）"):
            params = {
                "_t": current_timestamp_seconds,
                "broker_id": broker_id,
                "pageSize": "50"
            }
            response = self.send_get_request(
                logged_session, '/online/cgform/api/getData/402883917b2f2594017b335d3ddb0001', params=params
            )

            # 修复：移除error_msg参数
            self.assert_json_value(response, "$.success", True)
            all_servers = self.json_utils.extract(response.json(), "$.result.records[*]", multi_match=True, default=[])
            existing_servers = [s.get("server") for s in all_servers if s.get("server")]

            server_id = None
            for server in all_servers:
                if server.get("server") == target_server:
                    server_id = server.get("id")
                    break
            assert server_id is not None, f"未找到服务器[{target_server}]，当前服务器列表：{existing_servers}"
            return server_id

    def _extract_jeecg_row_key(self, logged_session):
        """提取全局MT4审核JeecgRowKey（共用方法）"""
        with allure.step("提取MT4审核JeecgRowKey"):
            params = {
                "_t": current_timestamp_seconds,
                "column": "name",
                "order": "asc"
            }
            response = self.send_get_request(
                logged_session, '/online/cgform/api/getData/4028839781b865e40181b87163350007', params=params
            )

            # 修复：移除error_msg参数
            self.assert_json_value(response, "$.success", True)
            jeecg_row_key = self.json_utils.extract(response.json(), "$.result.records[4].jeecg_row_key")
            assert jeecg_row_key is not None, "未提取到JeecgRowKey"
            return jeecg_row_key

    def _bind_account(self, logged_session, var_manager, current_acc, current_pwd, expect_success):
        """账号绑定（支持首次/重复绑定，读取全局变量）"""
        step_title = f"{'首次绑定' if expect_success else '重复绑定'}账号-{current_acc}"
        with allure.step(step_title):
            # 读取全局变量（用户ID、BrokerID、服务器ID）
            global_user_id = var_manager.get_variable(GLOBAL_USER_ID)
            global_broker_id = var_manager.get_variable(GLOBAL_BROKER_ID)
            global_server_id = var_manager.get_variable(GLOBAL_SERVER_ID)

            # 构造请求数据
            data = {
                "userId": global_user_id,
                "brokerId": global_broker_id,
                "serverId": global_server_id,
                "account": current_acc,
                "password": current_pwd,
                "display": "PRIVATE",
                "passwordType": "0",
                "subscribeFee": "0",
                "type": "SLAVE_REAL",
                "platform": "4"
            }

            # 发送请求并附加请求数据到报告
            response = self.send_post_request(logged_session, '/blockchain/account/bind', json_data=data)
            allure.attach(json.dumps(data, ensure_ascii=False, indent=2),
                          name=f"账号{current_acc}{'首次绑定' if expect_success else '重复绑定'}请求数据",
                          attachment_type=allure.attachment_type.JSON)

            # 修复：移除error_msg参数，通过assert上下文提示失败原因
            self.assert_json_value(response, "$.success", expect_success)
            # 重复绑定时，校验错误提示
            if not expect_success:
                self.assert_json_value(response, "$.message", "该账号在系统中已经被绑定了")

    def _extract_mt4_audit_id(self, logged_session, var_manager, current_acc):
        """提取账号专属MT4审核ID"""
        with allure.step(f"提取账号{current_acc}的MT4审核ID"):
            params = {
                "_t": current_timestamp_seconds,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "superQueryMatchType": "and",
                "status": "PENDING,VERIFICATION"
            }
            response = self.send_get_request(
                logged_session, '/online/cgform/api/getData/2c9a814a81d3a91b0181d3a91b250000', params=params
            )

            # 修复：移除error_msg参数
            self.assert_json_value(response, "$.success", True)
            all_records = self.json_utils.extract(response.json(), "$.result.records[*]", multi_match=True, default=[])
            existing_accounts = [r.get("account") for r in all_records if r.get("account")]

            # 匹配当前账号的审核ID
            follow_pass_id = None
            for record in all_records:
                if record.get("account") == current_acc:
                    follow_pass_id = record.get("id")
                    break
            assert follow_pass_id is not None, f"未找到账号{current_acc}的MT4审核记录，当前审核账号列表：{existing_accounts}"
            return follow_pass_id

    def _pass_mt4_audit(self, logged_session, var_manager, current_acc):
        """MT4审核通过（读取账号专属审核ID）- 核心修复点"""
        with allure.step(f"账号{current_acc}MT4审核通过"):
            # 1. 读取变量（全局变量+账号专属变量）
            follow_pass_id_key = FOLLOW_PASS_ID_TPL.format(acc=current_acc)
            follow_pass_id = var_manager.get_variable(follow_pass_id_key)  # 读取账号专属审核ID
            global_jeecg_row_key = var_manager.get_variable(GLOBAL_JEECG_ROW_KEY)
            global_vps_ip = var_manager.get_variable(GLOBAL_VPS_IP)

            # 2. 参数校验
            assert follow_pass_id is not None, f"账号{current_acc}的MT4审核ID（{follow_pass_id_key}）未找到"
            assert global_jeecg_row_key is not None, f"全局变量{GLOBAL_JEECG_ROW_KEY}未找到"
            assert global_vps_ip is not None, f"全局变量{GLOBAL_VPS_IP}未找到"

            # 3. 构造请求数据
            data = {
                "pass": True,
                "commission": False,
                "planId": global_jeecg_row_key,
                "toSynDate": DATETIME_NOW,
                "bindIpAddr": global_vps_ip
            }

            # 4. 发送审核通过请求
            response = self.send_post_request(
                logged_session=logged_session,
                url=f'/blockchain/account/pass/{follow_pass_id}',
                json_data=data
            )

            # 5. 响应校验+报告附加（核心修复：移除error_msg参数）
            self.assert_json_value(
                response=response,
                json_path="$.success",
                expected_value=True
            )
            allure.attach(
                json.dumps(data, ensure_ascii=False, indent=2),
                name=f"账号{current_acc}审核通过请求数据",
                attachment_type=allure.attachment_type.JSON
            )
            allure.attach(
                response.text,
                name=f"账号{current_acc}审核通过响应",
                attachment_type=allure.attachment_type.TEXT
            )

    def _clean_subscribe_record(self, logged_session, current_acc):
        """清理当前账号的历史订阅记录"""
        with allure.step(f"清理账号{current_acc}的历史订阅记录"):
            params = {
                "_t": current_timestamp_seconds,
                "account": current_acc,
                "pageNo": 1,
                "pageSize": 100,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

            # 修复：移除error_msg参数
            self.assert_json_value(response, "$.success", True)
            records = self.json_utils.extract(response.json(), "$.result.data.records[*]", multi_match=True, default=[])

            if records:
                # 提取并删除所有历史订阅记录
                for record in records:
                    delete_id = record.get("id")
                    if delete_id:
                        self.send_delete_request(
                            logged_session,
                            '/blockchain/master-slave/deletePa',
                            json_data={"id": delete_id}
                        )
                        logging.info(f"账号{current_acc}删除历史订阅记录（ID：{delete_id}）")
                allure.attach(f"已清理{len(records)}条历史订阅记录", name=f"账号{current_acc}订阅清理结果")
            else:
                allure.attach("无历史订阅记录，无需清理", name=f"账号{current_acc}订阅清理结果")

    def _subscribe_follow(self, logged_session, var_manager, current_acc):
        """订阅跟单（读取账号专属审核ID）"""
        with allure.step(f"账号{current_acc}订阅跟单"):
            # 1. 读取变量（全局变量+账号专属变量）
            global_trader_pass_id = var_manager.get_variable(GLOBAL_TRADER_PASS_ID)
            follow_pass_id_key = FOLLOW_PASS_ID_TPL.format(acc=current_acc)
            follow_pass_id = var_manager.get_variable(follow_pass_id_key)

            # 2. 参数校验
            assert global_trader_pass_id is not None, f"全局变量{GLOBAL_TRADER_PASS_ID}未找到"
            assert follow_pass_id is not None, f"账号{current_acc}的审核ID（{follow_pass_id_key}）未找到"

            # 3. 构造请求数据
            data = {
                "masterId": global_trader_pass_id,
                "slaveId": follow_pass_id,
                "direction": "FORWARD",
                "followingMode": "2",
                "fixedProportion": "100",
                "fixedLots": None,
                "order": {"paymentAccount": "", "paymentMethod": ""},
            }

            # 4. 发送订阅请求
            response = self.send_post_request(
                logged_session, '/blockchain/master-slave/admin/add', json_data=data
            )

            # 5. 响应校验+提取订阅ID（修复：移除error_msg参数）
            self.assert_json_value(response, "$.success", True)
            subscribe_id = self.json_utils.extract(response.json(), "$.result.id")
            assert subscribe_id is not None, f"账号{current_acc}订阅ID提取失败"

            # 附加订阅数据到报告
            allure.attach(
                json.dumps(data, ensure_ascii=False, indent=2),
                name=f"账号{current_acc}订阅请求数据",
                attachment_type=allure.attachment_type.JSON
            )
            return subscribe_id

    def _verify_subscribe_record(self, logged_session, var_manager, current_acc, expect_exist):
        """校验订阅记录是否存在（账号专属校验）"""
        with allure.step(f"校验账号{current_acc}的订阅记录"):
            params = {
                "_t": current_timestamp_seconds,
                "account": current_acc,
                "pageNo": 1,
                "pageSize": 100,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

            # 修复：移除error_msg参数
            self.assert_json_value(response, "$.success", True)
            records = self.json_utils.extract(response.json(), "$.result.data.records[*]", multi_match=True, default=[])

            # 保存订阅记录ID（账号专属）
            if records:
                jeecg_rowkey = records[0].get("jeecg_row_key")
                var_manager.set_runtime_variable(FOLLOW_JEECG_ROWKEY_TPL.format(acc=current_acc), jeecg_rowkey)

            # 存在性校验
            if expect_exist:
                assert records, f"账号{current_acc}未查询到订阅记录，订阅失败"
                allure.attach(f"查询到{len(records)}条订阅记录，符合预期", name=f"账号{current_acc}订阅校验结果")
            else:
                assert not records, f"账号{current_acc}仍存在订阅记录，清理失败"
                allure.attach("未查询到订阅记录，符合预期", name=f"账号{current_acc}订阅校验结果")
