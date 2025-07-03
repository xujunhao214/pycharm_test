# lingkuan_702/tests/test_delete.py
import allure
import pytest
import logging
from lingkuan_702.conftest import var_manager
from lingkuan_702.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestDeleteTrader(APITestBase):
    # ---------------------------
    # 跟单软件看板-VPS数据-删除跟单账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
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

    # ---------------------------
    # 批量删除跟单账号（循环删除）
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("跟单软件看板-VPS数据-批量删除跟单账号")
    def test_delete_addsalvelist(self, vps_api_session, var_manager, logged_session, db_transaction):
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
                    vps_api_session,
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
                if db_data:
                    # 逻辑删除：验证deleted字段为1
                    assert db_data[0]["deleted"] == 1, (
                        f"第{i}个账号（{account}）删除标记错误，"
                        f"应为1实际为{db_data[0]['deleted']}"
                    )
                    logger.info(f"第{i}个账号（{account}）逻辑删除验证通过")
                else:
                    # 物理删除：验证记录不存在
                    logger.info(f"第{i}个账号（{account}）物理删除验证通过")

                # 验证订阅表是否同步删除
                table_subscribe = db_addslave_query["table_subscribe"]
                sql_sub = f"SELECT * FROM {table_subscribe} WHERE slave_account = %s"
                db_data_sub = self.query_database(db_transaction, sql_sub, (account,))
                assert not db_data_sub, (
                    f"第{i}个账号（{account}）的订阅表记录未删除，"
                    f"残留数据：{db_data_sub}"
                )

    # ---------------------------
    # 跟单软件看板-VPS数据-删除策略账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
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
    # @pytest.mark.skip(reason=SKIP_REASON)
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


