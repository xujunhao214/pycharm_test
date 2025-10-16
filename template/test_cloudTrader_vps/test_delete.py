import time
import pytest
import logging
import allure
from typing import Dict, Any, List
from template.VAR.VAR import *
from template.conftest import var_manager
from template.commons.api_vpsbase import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("数据管理-删除跟单社区测试数据")
class TestDeleteUser(APIVPSBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-组别列表-删除VPS组别")
    def test_delete_group(self, logged_vps, var_manager):
        # 1. 发送删除VPS组别请求
        vps_group_id = var_manager.get_variable("vps_group_id")
        response = self.send_delete_request(
            logged_vps,
            "/mascontrol/group",
            json_data=[vps_group_id]
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "删除vps组别失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.retry(n=3, delay=5)
    @allure.title("数据库校验-组别列表-删除VPS组别")
    def test_dbdelete_group(self, var_manager, dbvps_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            add_vpsgroup = var_manager.get_variable("add_vpsgroup")
            sql = f"SELECT * FROM follow_group WHERE name = %s"
            params = (add_vpsgroup["name"],)
            try:
                self.wait_for_database_deletion(
                    dbvps_transaction=dbvps_transaction,
                    sql=sql,
                    params=params
                )
                allure.attach(f"VPS组别 {add_vpsgroup['name']} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

    @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-删除跟单账号")
    def test_delete_addsalve(self, var_manager, logged_vps):
        # 1. 发送删除跟单账号请求
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        response = self.send_delete_request(
            logged_vps,
            '/subcontrol/trader',
            json_data=[vps_addslave_id]
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "删除跟单账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-删除跟单账号")
    def test_dbdelete_addsalve(self, var_manager, dbvps_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            vps_user_accounts_2 = var_manager.get_variable("vps_user_accounts_2")
            logging.info(f"查询条件: table=follow_trader, account={vps_user_accounts_2}")

            sql = f"SELECT * FROM follow_trader WHERE account = %s"
            params = (vps_user_accounts_2,)
            try:
                self.wait_for_database_deletion(
                    dbvps_transaction=dbvps_transaction,
                    sql=sql,
                    params=params
                )
                allure.attach(f"跟单账号 {vps_user_accounts_2} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

            db_data2 = self.query_database(
                dbvps_transaction,
                f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s",
                (vps_user_accounts_2,))
            if db_data2:
                slave_account = db_data2[0]["slave_account"]
                assert slave_account is None, f"账号删除失败，表里还存在数据:{slave_account}"

    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-删除策略账号")
    def test_delete_vpstrader(self, var_manager, logged_vps):
        # 1. 发送删除策略账号请求
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        response = self.send_delete_request(
            logged_vps,
            '/subcontrol/trader',
            json_data=[vps_trader_id]
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "删除策略账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-删除策略账号")
    def test_dbdelete_vpstrader(self, var_manager, dbvps_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
            logging.info(f"查询条件: table=follow_trader, account={vps_user_accounts_1}")

            sql = f"SELECT * FROM follow_trader WHERE account = %s"
            params = (vps_user_accounts_1,)
            try:
                self.wait_for_database_deletion(
                    dbvps_transaction=dbvps_transaction,
                    sql=sql,
                    params=params
                )
                allure.attach(f"策略账号 {vps_user_accounts_1} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量删除账号")
    def test_delete_userlist(self, logged_vps, var_manager):
        """测试批量删除用户接口"""
        # 1. 获取需要删除的账号总数（从新增阶段的变量获取，确保与新增数量一致）
        vps_user_count = var_manager.get_variable("vps_user_count", 0)
        if vps_user_count <= 0:
            pytest.fail("未找到需要删除的账号总数，请检查前置步骤")

        # 2. 循环删除每个账号
        for i in range(1, vps_user_count + 1):
            with allure.step(f"删除第{i}个账号"):
                # 获取单个账号ID（vps_user_ids_1, vps_user_ids_2, vps_user_ids_3）
                user_id = var_manager.get_variable(f"vps_user_ids_{i}")
                if not user_id:
                    pytest.fail(f"未找到第{i}个账号的ID（变量名：vps_user_ids_{i}）")

                # 发送删除请求（接口支持传入ID列表，这里单次删除一个）
                response = self.send_delete_request(
                    logged_vps,
                    "/mascontrol/user",
                    json_data=[user_id]  # 保持接口要求的列表格式
                )

                # 3. 验证响应状态码
                self.assert_response_status(
                    response,
                    200,
                    f"删除第{i}个账号（ID: {user_id}）失败"
                )

                # 4. 验证响应内容
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    f"第{i}个账号删除响应msg字段应为success"
                )

                logging.info(f"第{i}个账号（ID: {user_id}）删除接口调用成功")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-批量删除账号")
    def test_dbdelete_userlist(self, var_manager, dbvps_transaction):
        """数据库校验批量删除结果"""
        # 1. 获取账号总数和数据库查询配置
        vps_user_count = var_manager.get_variable("vps_user_count", 0)
        if vps_user_count <= 0:
            pytest.fail("未找到需要验证的账号总数，请检查前置步骤")

        # 2. 循环验证每个账号的删除状态
        for i in range(1, vps_user_count + 1):
            with allure.step(f"验证第{i}个账号的删除状态"):
                # 获取当前账号的ID和账号名（用于数据库查询）
                account = var_manager.get_variable(f"vps_user_accounts_{i}")  # 账号名，如119999353
                if not account:
                    pytest.fail(f"未找到第{i}个账号的账号名（变量名：vps_user_accounts_{i}）")

                # 3. 执行数据库查询（按账号名查询，更直观）
                sql = f"SELECT * FROM FOLLOW_TRADER_USER WHERE account = %s"
                params = (account,)

                try:
                    self.wait_for_database_deletion(
                        dbvps_transaction=dbvps_transaction,
                        sql=sql,
                        params=params
                    )
                    allure.attach(f"账号 {account} 已成功从数据库删除", "验证结果")
                except TimeoutError as e:
                    allure.attach(f"删除超时: {str(e)}", "验证结果")
                    pytest.fail(f"删除失败: {str(e)}")
