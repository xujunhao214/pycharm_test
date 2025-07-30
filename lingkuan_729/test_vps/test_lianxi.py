import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_729.VAR.VAR import *
from lingkuan_729.conftest import var_manager
from lingkuan_729.commons.api_base import APITestBase  # 导入基础类
from lingkuan_729.commons.redis_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestDeleteFollowSlave(APITestBase):
    # ---------------------------
    # VPS管理-VPS列表-校验服务器IP是否可用
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表-校验服务器IP是否可用")
    def test_get_connect(self, api_session, var_manager, logged_session):
        # 1. 校验服务器IP是否可用
        add_VPS = var_manager.get_variable("add_VPS")
        response = self.send_get_request(
            api_session,
            '/mascontrol/vps/connect',
            params={'ipAddress': add_VPS["ipAddress"]}
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "服务器IP不可用"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # VPS管理-VPS列表-获取可见用户信息
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表-获取可见用户信息")
    def test_get_user(self, api_session, var_manager, logged_session):
        # 1. 请求可见用户列表接口
        response = self.send_get_request(
            api_session,
            '/sys/role/role'
        )

        # 2. 获取可见用户信息
        user_data = response.extract_jsonpath("$.data")
        logging.info(f"获取的可见用户信息：{user_data}")
        var_manager.set_runtime_variable("user_data", user_data)

    # ---------------------------
    # VPS管理-VPS列表-新增vps
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表-新增vps")
    def test_create_vps(self, api_session, var_manager, logged_session):
        # 1. 发送新增vps请求
        add_VPS = var_manager.get_variable("add_VPS")
        user_data = var_manager.get_variable("user_data")
        group_id = var_manager.get_variable("group_id")
        data = {
            "ipAddress": add_VPS["ipAddress"],
            "name": "测试",
            "expiryDate": DATETIME_ENDTIME,
            "remark": "测试VPS",
            "isOpen": 1,
            "isActive": 1,
            "roleList": user_data,
            "isSelectAccount": 1,
            "isMonitorRepair": 1,
            "isSpecializedRepair": 1,
            "isAutoRepair": 1,
            "groupId": f"{group_id}",
            "sort": 1000
        }
        response = self.send_post_request(
            api_session,
            '/mascontrol/vps',
            json_data=data,

        )

        # 2. 判断是否添加成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # 数据库校验-VPS列表-新增vps
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS列表-新增vps")
    def test_dbquery_vps(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            add_VPS = var_manager.get_variable("add_VPS")

            # 定义数据库查询条件
            sql = f"SELECT * FROM follow_vps WHERE ip_address=%s AND deleted=%s"
            params = (add_VPS["ipAddress"], add_VPS["deleted"])

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.query_database(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vps_list_id = db_data[0]["id"]
            logging.info(f"新增vps的id: {vps_list_id}")
            var_manager.set_runtime_variable("vps_list_id", vps_list_id)
