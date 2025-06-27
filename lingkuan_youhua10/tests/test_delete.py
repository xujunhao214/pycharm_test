# lingkuan_youhua10/tests/test_delete.py
import allure
import logging
import time
import pytest

from lingkuan_youhua10.conftest import var_manager

logger = logging.getLogger(__name__)


@allure.feature("账号管理-删除")
class TestDelete:
    # ---------------------------
    # 账号管理-账号列表-删除账号
    # ---------------------------
    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("账号管理-账号列表-删除账号")
    def test_delete_user(self, api_session, var_manager, logged_session, db_transaction):
        """测试删除用户接口"""
        with allure.step("1. 发送删除用户请求"):
            user_id = var_manager.get_variable("user_id")
            data = [user_id]
            response = api_session.delete('/mascontrol/user', json=data)
            time.sleep(3)

        with allure.step("2. 验证响应状态码"):
            assert response.status_code == 200, f"删除用户失败: {response.text}"

        with allure.step("3. 验证JSON返回内容"):
            # 使用JSONPath提取并断言
            msg = response.extract_jsonpath("$.msg")
            assert msg == "success", "响应msg字段应为success"

    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-账号列表-删除账号")
    def test_dbdelete_user(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            db_query = var_manager.get_variable("db_query")
            logging.info(f"查询条件: table={db_query['table']}, name={db_query['account']}")

            with db_transaction.cursor() as cursor:
                sql = f'SELECT * FROM {db_query["table"]} WHERE account = %s'
                try:
                    cursor.execute(sql, (db_query["account"],))
                    result = cursor.fetchone()
                    logging.info(f"数据库查询结果: {result}")

                    # 核心断言逻辑
                    if result:
                        # 检查删除标记（deleted字段）
                        assert result["deleted"] == 1, f"删除标记错误，应为1实际为{result['deleted']}"
                        logging.info(f"逻辑删除成功，deleted标记已更新为1")
                    else:
                        # 记录不存在时的断言
                        logging.info("物理删除成功，记录已不存在")

                except Exception as e:
                    logging.error(f"查询数据库错误: {str(e)}")
                    pytest.fail(f"数据库查询失败: {str(e)}")

    # ---------------------------
    # 账号管理-组别列表-删除VPS组别
    # ---------------------------
    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("账号管理-组别列表-删除VPS组别")
    def test_delete_group(self, api_session, var_manager, logged_session, db_transaction):
        """测试删除用户接口"""
        with allure.step("1. 发送删除VPS组别请求"):
            group_id = var_manager.get_variable("group_id")
            data = [group_id]
            response = api_session.delete('/mascontrol/group', json=data)
            time.sleep(3)

        with allure.step("2. 验证响应状态码"):
            assert response.status_code == 200, f"删除vps组别失败: {response.text}"

        with allure.step("3. 验证JSON返回内容"):
            # 使用JSONPath提取并断言
            msg = response.extract_jsonpath("$.msg")
            assert msg == "success", "响应msg字段应为success"

    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-组别列表-删除VPS组别")
    def test_dbdelete_group(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            db_group = var_manager.get_variable("db_group")
            logging.info(f"查询条件: table={db_group['table']}, name={db_group['name']}")

            with db_transaction.cursor() as cursor:
                sql = f'SELECT * FROM {db_group["table"]} WHERE name = %s'
                try:
                    cursor.execute(sql, (db_group["name"],))
                    result = cursor.fetchone()
                    logging.info(f"数据库查询结果: {result}")

                    # 核心断言逻辑
                    if result:
                        # 检查删除标记（deleted字段）
                        assert result["deleted"] == 1, f"删除标记错误，应为1实际为{result['deleted']}"
                        logging.info(f"逻辑删除成功，deleted标记已更新为1")
                    else:
                        # 记录不存在时的断言
                        logging.info("物理删除成功，记录已不存在")

                except Exception as e:
                    logging.error(f"查询数据库错误: {str(e)}")
                    pytest.fail(f"数据库查询失败: {str(e)}")

    # ---------------------------
    # 平台管理-品种管理-删除品种
    # ---------------------------
    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("平台管理-品种管理-删除品种")
    def test_deleteTemplate(self, api_session, var_manager, logged_session, db_transaction):
        """测试删除用户接口"""
        with allure.step("1. 发送删除品种请求"):
            template_id = var_manager.get_variable("template_id")
            response = api_session.delete('/mascontrol/variety/deleteTemplate', json=[template_id])
            time.sleep(3)

        with allure.step("2. 验证响应状态码"):
            assert response.status_code == 200, f"删除vps组别失败: {response.text}"

        with allure.step("3. 验证JSON返回内容"):
            # 使用JSONPath提取并断言
            msg = response.extract_jsonpath("$.msg")
            assert msg == "success", "响应msg字段应为success"

    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-品种管理-删除品种")
    def test_dbdelete_template(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            addvariety = var_manager.get_variable("addvariety")
            logging.info(f"查询条件: table={addvariety['table']}, template_name={addvariety['template_name']}")

            with db_transaction.cursor() as cursor:
                sql = f'SELECT * FROM {addvariety["table"]} WHERE template_name = %s'
                try:
                    cursor.execute(sql, (addvariety["template_name"],))
                    result = cursor.fetchone()
                    logging.info(f"数据库查询结果: {result}")

                    # 核心断言逻辑
                    if result:
                        # 检查删除标记（deleted字段）
                        assert result["deleted"] == 1, f"删除标记错误，应为1实际为{result['deleted']}"
                        logging.info(f"逻辑删除成功，deleted标记已更新为1")
                    else:
                        # 记录不存在时的断言
                        logging.info("物理删除成功，记录已不存在")

                except Exception as e:
                    logging.error(f"查询数据库错误: {str(e)}")
                    pytest.fail(f"数据库查询失败: {str(e)}")

    # ---------------------------
    # VPS管理-VPS列表列表-删除VPS
    # ---------------------------
    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("VPS管理-VPS列表列表-清空VPS数据")
    def test_deleteVps(self, api_session, var_manager, logged_session, db_transaction):
        vps_list_id = var_manager.get_variable("vps_list_id")
        # 定义白名单（不可清空数据的ID列表）
        WHITE_LIST_IDS = ["6", "91", "22", "49"]
        if vps_list_id in WHITE_LIST_IDS:
            logging.warning(f"VPS ID {vps_list_id} 在白名单中，跳过清空数据操作。")
            assert False, f"VPS ID {vps_list_id} 在白名单中，不能清空数据。"
        with allure.step("1. 发送清空VPS数据请求"):
            params = {
                "vpsId": f"{vps_list_id}"
            }
            response = api_session.get('/mascontrol/vps/deleteVps', params=params)
            time.sleep(3)

        with allure.step("2. 验证响应状态码"):
            assert response.status_code == 200, f"清空VPS数据失败: {response.text}"

        with allure.step("3. 验证JSON返回内容"):
            # 使用JSONPath提取并断言
            msg = response.extract_jsonpath("$.msg")
            assert msg == "success", "响应msg字段应为success"

    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("VPS管理-VPS列表列表-删除VPS数据")
    def test_delete_Vps(self, api_session, var_manager, logged_session, db_transaction):
        vps_list_id = var_manager.get_variable("vps_list_id")
        # 定义白名单（不可删除数据的ID列表）
        WHITE_LIST_IDS = ["6", "91", "22", "49"]
        if vps_list_id in WHITE_LIST_IDS:
            logging.warning(f"VPS ID {vps_list_id} 在白名单中，跳过删除数据操作。")
            assert False, f"VPS ID {vps_list_id} 在白名单中，不能删除数据。"
        with allure.step("1. 发送删除VPS数据请求"):
            data = [vps_list_id]
            response = api_session.delete('/mascontrol/vps', json=data)
            time.sleep(3)

        with allure.step("2. 验证响应状态码"):
            assert response.status_code == 200, f"删除VPS数据失败: {response.text}"

        with allure.step("3. 验证JSON返回内容"):
            # 使用JSONPath提取并断言
            msg = response.extract_jsonpath("$.msg")
            assert msg == "success", "响应msg字段应为success"

    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-VPS列表列表-删除VPS")
    def test_dbdelete_vps(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            add_VPS = var_manager.get_variable("add_VPS")
            logging.info(f"查询条件: ipAddress={add_VPS['ipAddress']}, deleted={add_VPS['deleted']}")

            with db_transaction.cursor() as cursor:
                sql = f'select * from {add_VPS["table"]} where ip_address=%s and deleted=%s'
                try:
                    cursor.execute(sql, (add_VPS["ipAddress"], add_VPS["deleted"]))
                    result = cursor.fetchone()
                    logging.info(f"数据库查询结果: {result}")

                    # 核心断言逻辑
                    if result:
                        # 检查删除标记（deleted字段）
                        assert result["deleted"] == 1, f"删除标记错误，应为1实际为{result['deleted']}"
                        logging.info(f"逻辑删除成功，deleted标记已更新为1")
                    else:
                        # 记录不存在时的断言
                        logging.info("物理删除成功，记录已不存在")

                except Exception as e:
                    logging.error(f"查询数据库错误: {str(e)}")
                    pytest.fail(f"数据库查询失败: {str(e)}")

    # ---------------------------
    # 跟单软件看板-VPS数据-删除策略账号
    # ---------------------------
    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("跟单软件看板-VPS数据-删除策略账号")
    def test_delete_vpstrader(self, vps_api_session, var_manager, logged_session, db_transaction):
        """测试删除用户接口"""
        with allure.step("1. 发送删除策略账号请求"):
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            response = vps_api_session.delete('/subcontrol/trader', json=[vps_trader_id])
            time.sleep(3)

        with allure.step("2. 验证响应状态码"):
            assert response.status_code == 200, f"删除策略账号失败: {response.text}"

        with allure.step("3. 验证JSON返回内容"):
            # 使用JSONPath提取并断言
            msg = response.extract_jsonpath("$.msg")
            assert msg == "success", "响应msg字段应为success"

    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-VPS数据-删除策略账号")
    def test_dbdelete_vpstrader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            db_trader_query = var_manager.get_variable("db_trader_query")
            logging.info(f"查询条件: table={db_trader_query['table']}, account={db_trader_query['account']}")

            with db_transaction.cursor() as cursor:
                sql = f'SELECT * FROM {db_trader_query["table"]} WHERE account = %s'
                try:
                    cursor.execute(sql, (db_trader_query["account"],))
                    result = cursor.fetchone()
                    logging.info(f"数据库查询结果: {result}")

                    # 核心断言逻辑
                    if result:
                        # 检查删除标记（deleted字段）
                        assert result["deleted"] == 1, f"删除标记错误，应为1实际为{result['deleted']}"
                        logging.info(f"逻辑删除成功，deleted标记已更新为1")
                    else:
                        # 记录不存在时的断言
                        logging.info("物理删除成功，记录已不存在")

                except Exception as e:
                    logging.error(f"查询数据库错误: {str(e)}")
                    pytest.fail(f"数据库查询失败: {str(e)}")
