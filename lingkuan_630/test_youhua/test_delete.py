# lingkuan_630/tests/test_delete.py
import allure
import pytest
import logging
from lingkuan_630.conftest import var_manager
from lingkuan_630.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("账号管理-删除")
class TestDelete(APITestBase):
    # ---------------------------
    # 账号管理-账号列表-删除账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-删除账号")
    def test_delete_user(self, api_session, var_manager, logged_session, db_transaction):
        """测试删除用户接口"""
        # 1. 发送删除用户请求
        user_id = var_manager.get_variable("user_id")
        response = self.send_delete_request(
            api_session,
            "/mascontrol/user",
            json_data=[user_id]
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
    # 账号管理-组别列表-删除VPS组别
    # ---------------------------
    @pytest.mark.skip(reason=SKIP_REASON)
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
    @pytest.mark.skip(reason=SKIP_REASON)
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
    # 数据库校验-品种管理-删除品种
    # ---------------------------
    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-品种管理-删除品种")
    def test_dbdelete_template(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            addvariety = var_manager.get_variable("addvariety")
            logging.info(f"查询条件: table={addvariety['table']}, template_name={addvariety['template_name']}")

            sql = f"SELECT * FROM {addvariety['table']} WHERE template_name = %s"
            params = (addvariety["template_name"],)

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
    @pytest.mark.skip(reason=SKIP_REASON)
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
    @pytest.mark.skip(reason=SKIP_REASON)
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
    @pytest.mark.skip(reason=SKIP_REASON)
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

    # ---------------------------
    # 跟单软件看板-VPS数据-删除策略账号
    # ---------------------------
    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("跟单软件看板-VPS数据-删除策略账号")
    def test_delete_vpstrader(self, vps_api_session, var_manager, logged_session, db_transaction):
        # 1. 发送删除策略账号请求
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        response = self.send_delete_request(
            vps_api_session,
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
    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-删除策略账号")
    def test_dbdelete_vpstrader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            db_trader_query = var_manager.get_variable("db_trader_query")
            logging.info(f"查询条件: table={db_trader_query['table']}, account={db_trader_query['account']}")

            sql = f"SELECT * FROM {db_trader_query['table']} WHERE account = %s"
            params = (db_trader_query["account"],)

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
    # 跟单软件看板-VPS数据-删除跟单账号
    # ---------------------------
    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("跟单软件看板-VPS数据-删除跟单账号")
    def test_delete_addsalve(self, vps_api_session, var_manager, logged_session, db_transaction):
        # 1. 发送删除跟单账号请求
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        response = self.send_delete_request(
            vps_api_session,
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
    # 数据库校验-VPS数据-删除策略账号
    # ---------------------------
    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-删除跟单账号")
    def test_dbdelete_addsalve(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            db_addslave_query = var_manager.get_variable("db_addslave_query")
            logging.info(f"查询条件: table={db_addslave_query['table']}, account={db_addslave_query['account']}")

            sql = f"SELECT * FROM {db_addslave_query['table']} WHERE account = %s"
            params = (db_addslave_query["account"],)

            db_data = self.query_database(db_transaction, sql, params)

            if db_data:
                assert db_data[0]["deleted"] == 1, (
                    f"删除标记错误，应为1实际为{db_data[0]['deleted']}\n"
                    f"查询结果: {db_data}"
                )
                logging.info(f"逻辑删除成功，deleted标记已更新为1")
            else:
                logging.info("物理删除成功，记录已不存在")

            db_data2 = self.query_database(
                db_transaction,
                f"SELECT * FROM {db_addslave_query['table_subscribe']} WHERE slave_account = %s",
                (db_addslave_query["account"],))
            if db_data2:
                slave_account = db_data2[0]["slave_account"]
                assert slave_account is None, f"账号删除失败，表里还存在数据:{slave_account}"
