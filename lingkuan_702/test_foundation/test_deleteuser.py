import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_702.VAR.VAR import *
from lingkuan_702.conftest import var_manager
from lingkuan_702.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("删除基本账号")
class TestDeleteUser(APITestBase):
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

            # 核心断言逻辑
            if db_data:
                # 检查删除标记（deleted字段）
                assert db_data[0]["deleted"] == 1, (
                    f"删除标记错误，应为1实际为{db_data[0]['deleted']}\n"
                    f"查询结果: {db_data}"
                )
                logging.info(f"逻辑删除成功，deleted标记已更新为1")
            else:
                # 记录不存在时的断言
                logging.info("物理删除成功，记录已不存在")

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
                    # 逻辑删除：检查deleted字段是否为1（已删除）
                    assert db_data[0]["deleted"] == 1, (
                        f"第{i}个账号（ID: {user_id}，账号: {account}）删除标记错误，"
                        f"应为1（已删除），实际为{db_data[0]['deleted']}"
                    )
                    logging.info(f"第{i}个账号（ID: {user_id}）逻辑删除验证通过")
                else:
                    # 物理删除：确认记录已不存在
                    logging.info(f"第{i}个账号（ID: {user_id}，账号: {account}）物理删除验证通过")

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
    # @pytest.mark.skip(reason=SKIP_REASON)
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
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-品种管理-删除品种")
    def test_dbdelete_template(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            add_variety = var_manager.get_variable("add_variety")
            logging.info(f"查询条件: table={add_variety['table']}, templateName={add_variety['templateName']}")

            sql = f"SELECT * FROM {add_variety['table']} WHERE template_name = %s"
            params = (add_variety["templateName"],)

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

            if db_data:
                assert db_data[0]["deleted"] == 1, (
                    f"删除标记错误，应为1实际为{db_data[0]['deleted']}\n"
                    f"查询结果: {db_data}"
                )
                logging.info(f"逻辑删除成功，deleted标记已更新为1")
            else:
                logging.info("物理删除成功，记录已不存在")

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

            if db_data:
                assert db_data[0]["deleted"] == 1, (
                    f"删除标记错误，应为1实际为{db_data[0]['deleted']}\n"
                    f"查询结果: {db_data}"
                )
                logging.info(f"逻辑删除成功，deleted标记已更新为1")
            else:
                logging.info("物理删除成功，记录已不存在")
