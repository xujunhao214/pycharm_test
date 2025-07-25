import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_714.VAR.VAR import *
from lingkuan_714.conftest import var_manager
from lingkuan_714.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestDeleteFollowSlave(APITestBase):
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
            "remark": "测试",
            "isOpen": 1,
            "isActive": 1,
            "userList": [user_data],
            "isSelectAccount": 1,
            "isMonitorRepair": 1,
            "isSpecializedRepair": 1,
            "isAutoRepair": 1,
            "groupId": f"{group_id}",
            "sort": 120
        }
        response = self.send_post_request(
            api_session,
            '/mascontrol/vps',
            json_data=data
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

    # ---------------------------
    # VPS管理-VPS列表-获取要复制的VPS的ID
    # ---------------------------
    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表-获取要复制的VPS的ID")
    def test_get_vps_pageid(self, api_session, var_manager, logged_session):
        # 1. 请求VPS列表接口
        list_query = var_manager.get_variable("list_query")
        response = self.send_get_request(
            api_session,
            'mascontrol/vps/page',
            params=list_query
        )

        # 2. 获取要复制的VPS的ID
        vps_page_id = response.extract_jsonpath("$.data.list[1].id")
        logging.info(f"获取vps的id：{vps_page_id}")
        var_manager.set_runtime_variable("vps_page_id", vps_page_id)