import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan.VAR.VAR import *
from lingkuan.conftest import var_manager
from lingkuan.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("删除基本账号")
class TestDeleteUser(APITestBase):
    # ---------------------------
    # 批量删除跟单账号（循环删除）
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-批量删除跟单账号")
    def test_delete_addsalvelist(self, var_manager, logged_session, db_transaction):
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
                logger.info(f"第{i}个跟单账号（ID: {slave_id}）删除成功")

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

        db_addslave_query = var_manager.get_variable("db_addslave_query")
        table = db_addslave_query["table"]

        # 2. 循环验证每个账号的删除状态
        for i in range(1, addslave_count + 1):
            with allure.step(f"验证第{i}个账号是否删除成功"):
                # 获取单个账号（与删除的ID对应）
                account = var_manager.get_variable(f"user_accounts_{i}")
                if not account:
                    pytest.fail(f"未找到需要验证的账号：user_accounts_{i}")

                # 查询数据库（检查删除标记或记录是否存在）
                sql = f"SELECT * FROM {table} WHERE account = %s"
                db_data = self.query_database(db_transaction, sql, (account,))

                # 验证逻辑：根据实际业务判断（逻辑删除/物理删除）
                assert not db_data, "删除后查询结果不为空，正确删除之后，查询结果应该为空"

                # 验证订阅表是否同步删除
                table_subscribe = db_addslave_query["table_subscribe"]
                sql_sub = f"SELECT * FROM {table_subscribe} WHERE slave_account = %s"
                db_data_sub = self.query_database(db_transaction, sql_sub, (account,))
                assert not db_data_sub, (
                    f"第{i}个账号（{account}）的订阅表记录未删除，"
                    f"残留数据：{db_data_sub}"
                )

    # ---------------------------
    # 跟单软件看板-VPS数据-删除跟单账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-删除跟单账号")
    def test_delete_addsalve(self, var_manager, logged_session, db_transaction):
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
        time.sleep(30)

    # ---------------------------
    # 数据库校验-VPS数据-删除跟单账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-删除跟单账号")
    def test_dbdelete_addsalve(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            db_addslave_query = var_manager.get_variable("db_addslave_query")
            logging.info(f"查询条件: table={db_addslave_query['table']}, account={db_addslave_query['account']}")

            sql = f"SELECT * FROM {db_addslave_query['table']} WHERE account = %s"
            params = (db_addslave_query["account"],)

            db_data = self.query_database(db_transaction, sql, params)

            assert not db_data, "删除后查询结果不为空，正确删除之后，查询结果应该为空"

            db_data2 = self.query_database(
                db_transaction,
                f"SELECT * FROM {db_addslave_query['table_subscribe']} WHERE slave_account = %s",
                (db_addslave_query["account"],))
            if db_data2:
                slave_account = db_data2[0]["slave_account"]
                assert slave_account is None, f"账号删除失败，表里还存在数据:{slave_account}"

    # ---------------------------
    # 跟单软件看板-VPS数据-删除策略账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-删除策略账号")
    def test_delete_vpstrader(self, var_manager, logged_session, db_transaction):
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
            db_trader_query = var_manager.get_variable("db_trader_query")
            logging.info(f"查询条件: table={db_trader_query['table']}, account={db_trader_query['account']}")

            sql = f"SELECT * FROM {db_trader_query['table']} WHERE account = %s"
            params = (db_trader_query["account"],)

            db_data = self.query_database(db_transaction, sql, params)

            assert not db_data, "删除后查询结果不为空，正确删除之后，查询结果应该为空"

    # ---------------------------
    # 账号管理-账号列表-删除账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-删除账号")
    def test_delete_user(self, api_session, var_manager, logged_session, db_transaction):
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
        time.sleep(10)

    # ---------------------------
    # 数据库校验-账号列表-删除账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-删除账号")
    def test_dbdelete_user(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            db_query = var_manager.get_variable("db_query")
            logging.info(f"查询条件: table={db_query['table']}, name={db_query['account']}")

            # 定义数据库查询
            sql = f"SELECT * FROM {db_query['table']} WHERE account = %s"
            params = (db_query["account"],)

            # 执行查询
            db_data = self.query_database(db_transaction, sql, params)
            assert not db_data, "删除后查询结果不为空，正确删除之后，查询结果应该为空"

    # ---------------------------
    # 账号管理-账号列表-批量删除账号（参数化）
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量删除账号")
    def test_delete_userlist(self, api_session, var_manager, logged_session, db_transaction):
        """测试批量删除用户接口（参数化处理3个账号）"""
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
        """数据库校验批量删除结果（对应3个账号）"""
        # 1. 获取账号总数和数据库查询配置
        user_count = var_manager.get_variable("user_count", 0)
        if user_count <= 0:
            pytest.fail("未找到需要验证的账号总数，请检查前置步骤")

        db_query = var_manager.get_variable("db_query")
        if not db_query or "table" not in db_query:
            pytest.fail("数据库查询配置不完整（缺少table）")

        # 2. 循环验证每个账号的删除状态
        for i in range(1, user_count + 1):
            with allure.step(f"验证第{i}个账号的删除状态"):
                # 获取当前账号的ID和账号名（用于数据库查询）
                user_id = var_manager.get_variable(f"user_ids_{i}")
                account = var_manager.get_variable(f"user_accounts_{i}")  # 账号名，如119999353
                if not account:
                    pytest.fail(f"未找到第{i}个账号的账号名（变量名：user_accounts_{i}）")

                # 3. 执行数据库查询（按账号名查询，更直观）
                sql = f"SELECT * FROM {db_query['table']} WHERE account = %s"
                params = (account,)
                db_data = self.query_database(db_transaction, sql, params)

                # 4. 验证删除结果（逻辑删除/物理删除）
                if db_data:
                    assert not db_data, f"删除后查询结果不为空，正确删除之后，查询结果应该为空，查询结果：{db_data}"

    # ---------------------------
    # 账号管理-组别列表-删除VPS组别
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-组别列表-删除VPS组别")
    def test_delete_group(self, api_session, var_manager, logged_session, db_transaction):
        """测试删除用户接口"""
        # 1. 发送删除VPS组别请求
        group_id = var_manager.get_variable("group_id")
        response = self.send_delete_request(
            api_session,
            "/mascontrol/group",
            json_data=[group_id]
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

    # ---------------------------
    # 数据库校验-组别列表-删除VPS组别
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-组别列表-删除VPS组别")
    def test_dbdelete_group(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            db_group = var_manager.get_variable("db_group")
            logging.info(f"查询条件: table={db_group['table']}, name={db_group['name']}")

            sql = f"SELECT * FROM {db_group['table']} WHERE name = %s"
            params = (db_group["name"],)

            db_data = self.query_database(db_transaction, sql, params)

            if db_data:
                assert db_data[0]["deleted"] == 1, (
                    f"删除标记错误，应为1实际为{db_data[0]['deleted']}\n"
                    f"查询结果: {db_data}"
                )
                logging.info(f"逻辑删除成功，deleted标记已更新为1")
            else:
                logging.info("物理删除成功，记录已不存在")

    # ---------------------------
    # 平台管理-品种管理-删除品种
    # ---------------------------
    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("平台管理-品种管理-删除品种")
    def test_deleteTemplate(self, api_session, var_manager, logged_session, db_transaction):
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
    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-品种管理-删除品种")
    def test_dbdelete_template(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            add_variety = var_manager.get_variable("add_variety")
            logging.info(f"查询条件: table={add_variety['table']}, templateName={add_variety['templateName']}")
            sql = f"SELECT * FROM {add_variety['table']} WHERE template_name = %s"
            params = (add_variety["templateName"],)
            db_data = self.query_database(db_transaction, sql, params)
            assert not db_data, "删除后查询结果不为空，正确删除之后，查询结果应该为空"

    # ---------------------------
    # 平台管理-品种管理-删除品种
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("平台管理-品种管理-删除品种2")
    def test_deleteTemplate2(self, api_session, var_manager, logged_session, db_transaction):
        """测试删除用户接口"""
        # 1. 发送删除品种请求
        template_id2 = var_manager.get_variable("template_id2")
        response = self.send_delete_request(
            api_session,
            '/mascontrol/variety/deleteTemplate',
            json_data=[template_id2]
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
    @allure.title("数据库校验-品种管理-删除品种2")
    def test_dbdelete_template2(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            add_variety = var_manager.get_variable("add_variety")
            logging.info(f"查询条件: table={add_variety['table']}, templateName2={add_variety['templateName2']}")

            sql = f"SELECT * FROM {add_variety['table']} WHERE template_name = %s"
            params = (add_variety["templateName2"],)

            db_data = self.query_database(db_transaction, sql, params)

            assert not db_data, "删除后查询结果不为空，正确删除之后，查询结果应该为空"

    # ---------------------------
    # VPS管理-VPS列表列表-清空VPS数据
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表列表-清空VPS数据")
    def test_closeVps(self, api_session, var_manager, logged_session, db_transaction):
        vps_list_id = var_manager.get_variable("vps_list_id")
        # 定义白名单（不可清空数据的ID列表）
        WHITE_LIST_IDS = ["6", "91", "22", "49"]
        if vps_list_id in WHITE_LIST_IDS:
            logging.warning(f"VPS ID {vps_list_id} 在白名单中，跳过清空数据操作。")
            assert False, f"VPS ID {vps_list_id} 在白名单中，不能清空数据。"

        # 1. 发送清空VPS数据请求
        params = {"vpsId": f"{vps_list_id}"}
        response = self.send_get_request(
            api_session,
            '/mascontrol/vps/deleteVps',
            params=params
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "清空VPS数据失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # VPS管理-VPS列表列表-删除VPS数据
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表列表-删除VPS数据")
    def test_delete_Vps(self, api_session, var_manager, logged_session, db_transaction):
        vps_list_id = var_manager.get_variable("vps_list_id")
        # 定义白名单（不可删除数据的ID列表）
        WHITE_LIST_IDS = ["6", "91", "22", "49"]
        if vps_list_id in WHITE_LIST_IDS:
            logging.warning(f"VPS ID {vps_list_id} 在白名单中，跳过删除数据操作。")
            assert False, f"VPS ID {vps_list_id} 在白名单中，不能删除数据。"

        # 1. 发送删除VPS数据请求
        response = self.send_delete_request(
            api_session,
            '/mascontrol/vps',
            json_data=[vps_list_id]
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "删除VPS数据失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # 数据库校验-VPS列表列表-删除VPS
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS列表列表-删除VPS")
    def test_dbdelete_vps(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            add_VPS = var_manager.get_variable("add_VPS")
            logging.info(f"查询条件: ipAddress={add_VPS['ipAddress']}, deleted={add_VPS['deleted']}")

            sql = f"SELECT * FROM {add_VPS['table']} WHERE ip_address=%s AND deleted=%s"
            params = (add_VPS["ipAddress"], add_VPS["deleted"])

            db_data = self.query_database(db_transaction, sql, params)

            assert not db_data, "删除后查询结果不为空，正确删除之后，查询结果应该为空"
