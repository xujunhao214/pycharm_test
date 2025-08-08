# lingkuan_801UAT/tests/test_create.py
import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_801UAT.VAR.VAR import *
from lingkuan_801UAT.commons.jsonpath_utils import *
from lingkuan_801UAT.conftest import var_manager
from lingkuan_801UAT.commons.api_base import APITestBase  # 导入基础类


logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


# ---------------------------
# 修改模式、品种
# ---------------------------
@allure.feature("云策略策略下单-跟单修改模式、品种")
class TestVPSOrderSend_Scence(APITestBase):
    # ---------------------------
    # 跟单软件看板-VPS数据-获取VPSID
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("跟单软件看板-VPS数据-获取VPSID")
    def test_get_vpsID(self, var_manager, logged_session):
        # 初始化 JSONPath 工具类
        json_utils = JsonPathUtils()

        with allure.step("1. 发送获取VPSID的请求接口"):
            params = {
                "name": "",
                "ip": "",
                "groupIds": "",
                "account": "",
                "type": "0",
            }
            response = self.send_get_request(
                logged_session,
                '/mascontrol/vps/listVps',
                params=params
            )
            # 将响应转换为字典
            response_json = response.json()

        with allure.step("2. 校验接口请求是否正确"):
            # 使用工具类的 assert_value 方法验证响应状态
            json_utils.assert_value(
                response_json,
                "$.msg",
                "success",
            )

        with allure.step("3. 提取数据"):
            # 先提取所有 VPS 列表（避开过滤语法）
            vps_list = json_utils.extract(
                response_json,
                "$.data.list"  # 只提取列表，不做过滤
            )

            # 手动过滤出 name 为 ^主VPS 的对象
            target_vps = None
            for vps in vps_list:
                if vps.get("name") == "39.99.145.155-Allon专用张家口3":
                    target_vps = vps
                    break

            # 校验是否找到目标 VPS
            assert target_vps is not None, "未找到 name 为 '39.99.145.155-Allon专用张家口3' 的 VPS 数据"

            # 提取 id
            vpsId = target_vps.get("id")
            assert vpsId is not None, "找到的 VPS 数据中没有 id 字段"

            # 存入变量管理器
            var_manager.set_runtime_variable("vpsId", vpsId)
            print(f"成功提取 VPS ID: {vpsId}")