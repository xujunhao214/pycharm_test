import pytest
import allure
from typing import List, Dict
from lingkuan_631.commons.api_base import APITestBase  # 导入基础类


@allure.feature("跟单软件看板")
class TestFollowSlave(APITestBase):
    # 定义非account字段的参数模板（可根据需求扩展）
    _param_templates: List[Dict] = [
        {"followMode": 0, "followParam": "5.00", "templateId": 1, "desc": "默认模板-倍数5倍"},
        {"followMode": 1, "followParam": "1", "templateId": 1, "desc": "默认模板-固定1倍"},
        {"followMode": 0, "followParam": "2.50", "templateId": 38, "desc": "自定义模板-倍数2.5倍"}
    ]

    # 参数化测试用例（依赖数据库校验用例）
    @pytest.mark.dependency(depends=["test_dbquery__importuser"])  # 依赖数据提取用例
    @allure.title("跟单软件看板-VPS数据-新增跟单账号（多字段参数化）")
    @pytest.mark.parametrize(
        "param",
        # 动态生成参数：user_accounts中的每个账号 + 模板组合
        lambda self, var_manager: [
            {
                "account": account,
                "followMode": template["followMode"],
                "followParam": template["followParam"],
                "templateId": template["templateId"],
                "desc": f"账号{account}-{template['desc']}"
            }
            for account in var_manager.get_runtime_variable("user_accounts", [])
            for template in self._param_templates
        ],
        # 用例ID显示参数描述，便于报告区分
        ids=lambda param: param["desc"]
    )
    def test_create_addSlave(self, vps_api_session, var_manager, logged_session, db_transaction, param):
        # 1. 从参数中提取当前执行的字段值
        current_account = param["account"]
        current_mode = param["followMode"]
        current_param = param["followParam"]
        current_template = param["templateId"]

        # 2. 构造请求数据（动态替换四个参数）
        add_Slave = var_manager.get_variable("add_Slave")
        vps_trader_id = var_manager.get_variable("vps_trader_id")

        data = {
            "traderId": vps_trader_id,
            "platform": add_Slave["platform"],
            "account": current_account,  # 来自user_accounts的动态账号
            "password": add_Slave["password"],
            "remark": param["desc"],  # 备注包含参数信息，便于调试
            "followDirection": 0,
            "followMode": current_mode,  # 参数化字段1
            "remainder": 0,
            "followParam": current_param,  # 参数化字段2
            "placedType": 0,
            "templateId": current_template,  # 参数化字段3
            "followStatus": 1,
            "followOpen": 1,
            "followClose": 1,
            "followRep": 0,
            "fixedComment": add_Slave["fixedComment"],
            "commentType": 2,
            "digits": 0,
            "cfd": "",
            "forex": "",
            "abRemark": ""
        }

        # 3. 发送请求
        with allure.step(f"执行参数: {param['desc']}"):
            response = self.send_post_request(
                vps_api_session,
                '/subcontrol/follow/addSlave',
                json_data=data
            )

        # 4. 验证响应
        self.assert_response_status(
            response, 200,
            f"账号{current_account}新增失败（模式{current_mode}）"
        )
        self.assert_json_value(
            response, "$.msg", "success",
            f"账号{current_account}响应异常（模式{current_mode}）"
        )