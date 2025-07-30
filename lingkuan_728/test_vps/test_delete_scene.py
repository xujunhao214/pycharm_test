# lingkuan_728/tests/test_delete.py
import time

import allure
import pytest
import logging
from lingkuan_728.VAR.VAR import *
from lingkuan_728.conftest import var_manager
from lingkuan_728.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("删除跟单账号和策略账号")
class TestDeleteTrader(APITestBase):
    # ---------------------------
    # 跟单软件看板-VPS数据-删除跟单账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-删除跟单账号")
    def test_delete_addsalve(self, var_manager, logged_session):
        # 1. 发送删除跟单账号请求
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        response = self.send_delete_request(
            logged_session,
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

    # ---------------------------
    # 数据库校验-VPS数据-删除跟单账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-删除跟单账号")
    def test_dbdelete_addsalve(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            user_accounts_1 = var_manager.get_variable("user_accounts_1")
            logging.info(f"查询条件: table=follow_trader, account={user_accounts_1}")

            sql = f"SELECT * FROM follow_trader WHERE account = %s"
            params = (user_accounts_1,)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    timeout=DELETE_WAIT_TIMEOUT,  # 设置5秒超时时间
                    poll_interval=POLL_INTERVAL  # 每2秒查询一次
                )
                allure.attach(f"跟单账号 {user_accounts_1} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

            db_data2 = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s",
                (user_accounts_1,))
            if db_data2:
                slave_account = db_data2[0]["slave_account"]
                assert slave_account is None, f"账号删除失败，表里还存在数据:{slave_account}"

    # ---------------------------
    # 批量删除跟单账号（循环删除）
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-批量删除跟单账号")
    def test_delete_addsalvelist(self, var_manager, logged_session):
        # 1. 获取账号总数和所有ID
        addslave_count = var_manager.get_variable("addslave_count", 0)
        if addslave_count <= 0:
            pytest.fail("未找到需要删除的账号数量，请检查前置步骤")

        # 2. 循环获取每个账号的ID并删除
        for i in range(1, addslave_count + 1):
            with allure.step(f"删除第{i}个跟单账号"):
                # 获取单个账号ID（vps_addslave_ids_1, vps_addslave_ids_2, ...）
                slave_id = var_manager.get_variable(f"vps_addslave_ids_{i}")
                if not slave_id:
                    pytest.fail(f"未找到需要删除的账号ID：vps_addslave_ids_{i}")
                print(f"删除第{i}个跟单账号:vps_addslave_ids_{i}")

                # 发送删除请求（接口支持单个ID删除，参数为列表形式）
                response = self.send_delete_request(
                    logged_session,
                    '/subcontrol/trader',
                    json_data=[slave_id]  # 保持与接口要求一致的列表格式
                )

                # 验证响应
                self.assert_response_status(
                    response,
                    200,
                    f"删除第{i}个跟单账号（ID: {slave_id}）失败"
                )
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    f"第{i}个账号删除响应msg字段应为success"
                )
                logger.info(f"[{DATETIME_NOW}] 第{i}个跟单账号（ID: {slave_id}）删除成功")

    # ---------------------------
    # 数据库校验：批量验证删除结果
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-批量删除跟单账号")
    def test_dbdelete_addsalvelist(self, var_manager, db_transaction):
        # 1. 获取账号总数和所有账号信息
        addslave_count = var_manager.get_variable("addslave_count", 0)
        if addslave_count <= 0:
            pytest.fail("未找到需要验证的账号数量，请检查前置步骤")

        # 2. 循环验证每个账号的删除状态
        for i in range(1, addslave_count + 1):
            with allure.step(f"验证第{i}个账号是否删除成功"):
                # 获取单个账号（与删除的ID对应）
                account = var_manager.get_variable(f"user_accounts_{i}")
                if not account:
                    pytest.fail(f"未找到需要验证的账号：user_accounts_{i}")

                # 查询数据库（检查删除标记或记录是否存在）
                sql = f"SELECT * FROM follow_trader WHERE account = %s"
                # 调用轮询等待方法（带时间范围过滤）
                try:
                    self.wait_for_database_deletion(
                        db_transaction=db_transaction,
                        sql=sql,
                        params=(account,),
                        timeout=DELETE_WAIT_TIMEOUT,  # 设置5秒超时时间
                        poll_interval=POLL_INTERVAL  # 每2秒查询一次
                    )
                    allure.attach(f"跟单账号 {account} 已成功从数据库删除", "验证结果")
                except TimeoutError as e:
                    allure.attach(f"删除超时: {str(e)}", "验证结果")
                    pytest.fail(f"删除失败: {str(e)}")

                # 验证订阅表是否同步删除
                sql_sub = f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s"
                db_data_sub = self.query_database(db_transaction, sql_sub, (account,))
                assert not db_data_sub, (
                    f"第{i}个账号（{account}）的订阅表记录未删除，"
                    f"残留数据：{db_data_sub}"
                )

    # ---------------------------
    # 跟单软件看板-VPS数据-删除策略账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-删除策略账号")
    def test_delete_vpstrader(self, var_manager, logged_session):
        # 1. 发送删除策略账号请求
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        response = self.send_delete_request(
            logged_session,
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

    # ---------------------------
    # 数据库校验-VPS数据-删除策略账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-删除策略账号")
    def test_dbdelete_vpstrader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            new_user = var_manager.get_variable("new_user")
            logging.info(f"查询条件: table=follow_trader, account={new_user['account']}")

            sql = f"SELECT * FROM follow_trader WHERE account = %s"
            params = (new_user["account"],)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    timeout=DELETE_WAIT_TIMEOUT,  # 设置5秒超时时间
                    poll_interval=POLL_INTERVAL  # 每2秒查询一次
                )
                allure.attach(f"策略账号 {new_user['account']} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

    # ---------------------------
    # 平台管理-品种管理-删除品种
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("平台管理-品种管理-删除品种")
    def test_deleteTemplate(self, api_session, var_manager, logged_session):
        """测试删除用户接口"""
        # 1. 发送删除品种请求
        template_id = var_manager.get_variable("template_id")
        response = self.send_delete_request(
            api_session,
            '/mascontrol/variety/deleteTemplate',
            json_data=[template_id]
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "删除品种失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # 数据库校验-品种管理-删除品种
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-品种管理-删除品种")
    def test_dbdelete_template(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            add_variety = var_manager.get_variable("add_variety")
            logging.info(f"查询条件: table=follow_variety, templateName2={add_variety['templateName']}")

            sql = f"SELECT * FROM follow_variety WHERE template_name = %s"
            params = (add_variety["templateName"],)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    timeout=DELETE_WAIT_TIMEOUT,  # 设置5秒超时时间
                    poll_interval=POLL_INTERVAL  # 每2秒查询一次
                )
                allure.attach(f"品种 {add_variety['templateName']} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

    # ---------------------------
    # 账号管理-账号列表-删除账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-删除账号")
    def test_delete_user(self, api_session, var_manager, logged_session):
        """测试删除用户接口"""
        # 1. 发送删除用户请求
        trader_user_id = var_manager.get_variable("trader_user_id")
        response = self.send_delete_request(
            api_session,
            "/mascontrol/user",
            json_data=[trader_user_id]
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "删除用户失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # 数据库校验-账号列表-删除账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-删除账号")
    def test_dbdelete_user(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            new_user = var_manager.get_variable("new_user")
            logging.info(f"查询条件: table=FOLLOW_TRADER_USER, name={new_user['account']}")

            # 定义数据库查询
            sql = f"SELECT * FROM FOLLOW_TRADER_USER WHERE account = %s"
            params = (new_user["account"],)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    timeout=DELETE_WAIT_TIMEOUT,  # 设置5秒超时时间
                    poll_interval=POLL_INTERVAL  # 每2秒查询一次
                )
                allure.attach(f"账号 {new_user['account']} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

    # ---------------------------
    # 账号管理-账号列表-批量删除账号（参数化）
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量删除账号")
    def test_delete_userlist(self, api_session, var_manager, logged_session):
        """测试批量删除用户接口"""
        # 1. 获取需要删除的账号总数（从新增阶段的变量获取，确保与新增数量一致）
        user_count = var_manager.get_variable("user_count", 0)
        if user_count <= 0:
            pytest.fail("未找到需要删除的账号总数，请检查前置步骤")

        # 2. 循环删除每个账号
        for i in range(1, user_count + 1):
            with allure.step(f"删除第{i}个账号"):
                # 获取单个账号ID（user_ids_1, user_ids_2, user_ids_3）
                user_id = var_manager.get_variable(f"user_ids_{i}")
                if not user_id:
                    pytest.fail(f"未找到第{i}个账号的ID（变量名：user_ids_{i}）")

                # 发送删除请求（接口支持传入ID列表，这里单次删除一个）
                response = self.send_delete_request(
                    api_session,
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

    # ---------------------------
    # 数据库校验-批量删除账号（参数化）
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-批量删除账号")
    def test_dbdelete_userlist(self, var_manager, db_transaction):
        """数据库校验批量删除结果"""
        # 1. 获取账号总数和数据库查询配置
        user_count = var_manager.get_variable("user_count", 0)
        if user_count <= 0:
            pytest.fail("未找到需要验证的账号总数，请检查前置步骤")

        # 2. 循环验证每个账号的删除状态
        for i in range(1, user_count + 1):
            with allure.step(f"验证第{i}个账号的删除状态"):
                # 获取当前账号的ID和账号名（用于数据库查询）
                account = var_manager.get_variable(f"user_accounts_{i}")  # 账号名，如119999353
                if not account:
                    pytest.fail(f"未找到第{i}个账号的账号名（变量名：user_accounts_{i}）")

                # 3. 执行数据库查询（按账号名查询，更直观）
                sql = f"SELECT * FROM FOLLOW_TRADER_USER WHERE account = %s"
                params = (account,)

                try:
                    self.wait_for_database_deletion(
                        db_transaction=db_transaction,
                        sql=sql,
                        params=params,
                        timeout=DELETE_WAIT_TIMEOUT,  # 设置5秒超时时间
                        poll_interval=POLL_INTERVAL  # 每2秒查询一次
                    )
                    allure.attach(f"账号 {account} 已成功从数据库删除", "验证结果")
                except TimeoutError as e:
                    allure.attach(f"删除超时: {str(e)}", "验证结果")
                    pytest.fail(f"删除失败: {str(e)}")
