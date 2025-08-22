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


@allure.feature("数据管理-删除VPS测试数据")
class TestDeleteUser(APITestBase):
    # ---------------------------
    # 账号管理-组别列表-删除VPS组别
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-组别列表-删除VPS组别")
    def test_delete_group(self, logged_session, var_manager):
        # 1. 发送删除VPS组别请求
        vps_group_id = var_manager.get_variable("vps_group_id")
        response = self.send_delete_request(
            logged_session,
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

    # ---------------------------
    # 数据库校验-组别列表-删除VPS组别
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-组别列表-删除VPS组别")
    def test_dbdelete_group(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            add_vpsgroup = var_manager.get_variable("add_vpsgroup")
            sql = f"SELECT * FROM follow_group WHERE name = %s"
            params = (add_vpsgroup["name"],)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
                allure.attach(f"VPS组别 {add_vpsgroup['name']} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")

    # ---------------------------
    # VPS管理-VPS列表列表-清空VPS数据
    # ---------------------------
    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表列表-清空VPS数据")
    def test_closeVps(self, logged_session, var_manager):
        vps_list_id = var_manager.get_variable("vps_list_id")
        # 定义白名单（不可清空数据的ID列表）
        WHITE_LIST_IDS = var_manager.get_variable("WHITE_LIST")
        if vps_list_id in WHITE_LIST_IDS:
            logging.warning(f"VPS ID {vps_list_id} 在白名单中，跳过清空数据操作。")
            assert False, f"VPS ID {vps_list_id} 在白名单中，不能清空数据。"

        # 1. 发送清空VPS数据请求
        params = {"vpsId": f"{vps_list_id}"}
        response = self.send_get_request(
            logged_session,
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
    def test_delete_Vps(self, logged_session, var_manager):
        vps_list_id = var_manager.get_variable("vps_list_id")
        # 定义白名单（不可删除数据的ID列表）
        WHITE_LIST_IDS = var_manager.get_variable("WHITE_LIST")
        if vps_list_id in WHITE_LIST_IDS:
            logging.warning(f"VPS ID {vps_list_id} 在白名单中，跳过删除数据操作。")
            assert False, f"VPS ID {vps_list_id} 在白名单中，不能删除数据。"

        # 1. 发送删除VPS数据请求
        response = self.send_delete_request(
            logged_session,
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
        time.sleep(15)

    # ---------------------------
    # VPS管理-VPS列表列表-强制删除VPS
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表列表-强制删除VPS")
    def test_deleteVPS_forceDelete(self, logged_session, var_manager):
        vps_list_id = var_manager.get_variable("vps_list_id")
        # 定义白名单（不可删除数据的ID列表）
        WHITE_LIST_IDS = var_manager.get_variable("WHITE_LIST")
        if vps_list_id in WHITE_LIST_IDS:
            logging.warning(f"VPS ID {vps_list_id} 在白名单中，跳过删除数据操作。")
            assert False, f"VPS ID {vps_list_id} 在白名单中，不能删除数据。"

        params = {
            "idList": [
                vps_list_id
            ],
            "ignoreStop": 1
        }

        # 1. 发送强制删除VPS数据请求
        response = self.send_post_request(
            logged_session,
            '/mascontrol/vps/forceDelete',
            json_data=params
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
        time.sleep(15)

    # ---------------------------
    # 数据库校验-VPS列表列表-删除VPS
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS列表列表-删除VPS")
    def test_dbdelete_vps(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            add_VPS = var_manager.get_variable("add_VPS")
            logging.info(f"查询条件: ipAddress={add_VPS['ipAddress']}, deleted={add_VPS['deleted']}")

            sql = f"SELECT * FROM follow_vps WHERE ip_address=%s AND deleted=%s"
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
