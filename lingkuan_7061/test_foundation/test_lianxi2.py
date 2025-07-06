import pytest
import logging
import allure
import time
from typing import Dict, Any, List
from lingkuan_7061.VAR.VAR import *
from lingkuan_7061.conftest import var_manager
from lingkuan_7061.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestFollowSlave(APITestBase):
    # ---------------------------
    # 修改跟单账号-参数化测试（仅使用后6个数据）
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("修改跟单账号（仅使用后6个数据与模板匹配）")
    def test_update_addSlave(self, var_manager, logged_session, db_transaction):
        # 1. 获取总用户数（需确保至少有7个，才能取后6个）
        user_count = var_manager.get_variable("user_count", 0)
        if user_count < 7:
            pytest.fail(f"用户总数需至少为7，当前为{user_count}，无法提取后6个数据")

        # 2. 仅提取后6个账号（索引1~6，对应user_accounts_2~user_accounts_7）
        all_accounts = []
        for i in range(2, 8):  # 直接指定取2~7共6个账号
            account = var_manager.get_variable(f"user_accounts_{i}")
            if not account:
                pytest.fail(f"未找到第{i}个账号（变量：user_accounts_{i}）")
            all_accounts.append(account)
        print(f"已提取后6个账号：{all_accounts}")

        all_ids = []
        for i in range(1, 7):  # 直接指定取1~7共6个账号
            addslave_id = var_manager.get_variable(f"vps_addslave_ids_{i}")
            if not addslave_id:
                pytest.fail(f"未找到第{i}个账号（变量：vps_addslave_ids_{i}）")
            all_ids.append(addslave_id)
        print(f"已提取后6个账号id：{all_ids}")

        template_id2 = var_manager.get_variable("template_id2")

        # 3. 定义6个模板（与账号一一对应）
        templates: List[Dict[str, Any]] = [
            {
                "followMode": 0,
                "followParam": "5.00",
                "templateId": 1,
                "remark": "测试数据",
                "Cfd": "",
                "mode_desc": "固定手数（5倍）"
            },
            {
                "followMode": 1,
                "followParam": "1",
                "templateId": template_id2,
                "remark": "测试数据",
                "Cfd": "",
                "mode_desc": "修改品种（3倍）"
            },
            {
                "followMode": 2,
                "followParam": "1",
                "templateId": 1,
                "remark": "测试数据",
                "Cfd": "",
                "mode_desc": "净值比例"
            },
            {
                "followMode": 1,
                "followParam": "1",
                "templateId": 1,
                "remark": "测试数据",
                "Cfd": "@",
                "mode_desc": "修改币种，合约是100"
            },
            {
                "followMode": 1,
                "followParam": "1",
                "templateId": 1,
                "remark": "测试数据",
                "Cfd": ".p",
                "mode_desc": "修改币种，合约是100000"
            },
            {
                "followMode": 1,
                "followParam": "1",
                "templateId": 1,
                "remark": "测试数据",
                "Cfd": ".min",
                "mode_desc": "修改币种，合约是10"
            },
        ]

        # 4. 生成参数化数据（后6个账号与6个模板一一对应）
        parametrize_data = []
        for i in range(len(all_accounts)):
            account = all_accounts[i]
            id = all_ids[i]
            template = templates[i]  # 直接一一对应（账号1→模板1，账号2→模板2，...）
            parametrize_data.append({
                "account": account,
                "followMode": template["followMode"],
                "followParam": template["followParam"],
                "templateId": template["templateId"],
                "remark": template["remark"],  # 修改备注
                "Cfd": template["Cfd"],  # 修改Cfd参数
                "id": id,
                "desc": f"账号{account}-{template['mode_desc']}"
            })
        print(f"生成{len(parametrize_data)}条参数化测试数据（后6个账号）")

        # 5. 循环执行后6个账号的修改操作
        for param in parametrize_data:
            with allure.step(f"执行参数: {param['desc']}"):
                # 获取基础配置
                add_Slave = var_manager.get_variable("add_Slave")
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                password = var_manager.get_variable("password")

                # 构造请求数据
                data = {
                    "traderId": vps_trader_id,
                    "platform": add_Slave["platform"],
                    "account": param["account"],
                    "password": password,
                    "remark": param["remark"],  # 备注包含模板信息
                    "followMode": param["followMode"],
                    "followParam": param["followParam"],
                    "templateId": param["templateId"],
                    "followDirection": 0,
                    "remainder": 0,
                    "placedType": 0,
                    "followStatus": 1,
                    "followOpen": 1,
                    "followClose": 1,
                    "followRep": 0,
                    "fixedComment": add_Slave["fixedComment"],
                    "commentType": 2,
                    "digits": 0,
                    "cfd": param["Cfd"],  # 使用模板中的Cfd值
                    "forex": "",
                    "abRemark": "",
                    "id": param["id"]
                }

                # 发送请求并验证
                response = self.send_post_request(
                    logged_session, '/subcontrol/follow/updateSlave', json_data=data
                )

                self.assert_response_status(
                    response, 200,
                    f"账号{param['account']}修改失败（模板：{param['desc']}）"
                )
                self.assert_json_value(
                    response, "$.msg", "success",
                    f"账号{param['account']}响应异常（模板：{param['desc']}）"
                )
        time.sleep(15)
