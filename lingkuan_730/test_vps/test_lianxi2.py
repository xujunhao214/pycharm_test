import time
import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_730.VAR.VAR import *
from lingkuan_730.conftest import var_manager
from lingkuan_730.commons.api_base import APITestBase

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestDeleteFollowSlave(APITestBase):
    # ---------------------------
    # VPS管理-VPS列表列表-清空VPS数据
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表列表-清空VPS数据")
    def test_closeVps(self, api_session, var_manager, logged_session):
        vps_list_id = var_manager.get_variable("vps_list_id")
        # 定义白名单（不可清空数据的ID列表）
        WHITE_LIST_IDS = WHITE_LIST
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
    def test_delete_Vps(self, api_session, var_manager, logged_session):
        vps_list_id = var_manager.get_variable("vps_list_id")
        # 定义白名单（不可删除数据的ID列表）
        WHITE_LIST_IDS = WHITE_LIST
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
        time.sleep(15)

    # ---------------------------
    # VPS管理-VPS列表列表-强制删除VPS
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表列表-强制删除VPS")
    def test_deleteVPS_forceDelete(self, api_session, var_manager, logged_session):
        vps_list_id = var_manager.get_variable("vps_list_id")
        # 定义白名单（不可删除数据的ID列表）
        WHITE_LIST_IDS = WHITE_LIST
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
            api_session,
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
