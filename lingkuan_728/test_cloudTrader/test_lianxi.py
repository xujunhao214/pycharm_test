# lingkuan_728/tests/test_vps_ordersend.py
import time
import math
import allure
import logging
import pytest
from lingkuan_728.VAR.VAR import *
from lingkuan_728.conftest import var_manager
from lingkuan_728.commons.api_base import APITestBase

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


# ---------------------------
# 修改模式、品种
# ---------------------------
@allure.feature("云策略策略下单-跟单修改模式、品种")
class TestVPSOrderSend_Scence(APITestBase):
    # ---------------------------
    # 云策略-云策略列表-批量新增挂靠账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-批量新增云策略跟单账号")
    def test_create_importcloudBatchAdd(self, var_manager, logged_session):
        # 1. 获取账号总数和所有ID
        cloudMaster_id = var_manager.get_variable("cloudMaster_id")
        account_cloudTrader = var_manager.get_variable("account_cloudTrader", 0)
        if account_cloudTrader < 0:
            pytest.fail("未找到需要新增的账号数量，请检查前置步骤")
        # 2. 循环获取每个账号的ID
        for i in range(4, account_cloudTrader + 1):
            with allure.step(f"1. 获取第{i}个跟单账号的ID"):
                slave_id = var_manager.get_variable(f"vps_cloudTrader_ids_{i}")
                if not slave_id:
                    pytest.fail(f"第{i}个跟单账号的ID为空")
                print(f"获取第{i}个跟单账号的ID:vps_cloudTrader_ids_{i}")
                # 3. 发送新增跟单云策略请求（接口支持单个ID删除，参数为列表形式）
                data = {
                    "traderList": [
                        slave_id
                    ],
                    "remark": "新增云策略跟单账号",
                    "followDirection": 0,
                    "followMode": 1,
                    "remainder": 0,
                    "followParam": 1,
                    "placedType": 0,
                    "templateId": 1,
                    "followStatus": 1,
                    "followOpen": 1,
                    "followClose": 1,
                    "followRep": 0,
                    "fixedComment": "ceshi",
                    "commentType": "",
                    "digits": 0,
                    "cfd": "",
                    "forex": "",
                    "sort": None,
                    "cloudId": cloudMaster_id
                }
                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudBatchAdd',
                    json_data=data
                )

                # 2. 验证响应状态码
                self.assert_response_status(
                    response,
                    200,
                    "新增云策略跟单账号失败"
                )

                # 3. 验证JSON返回内容
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-批量新增云策略跟单账号")
    def test_dbquery_cloudBatchAdd(self, var_manager, db_transaction):
        # 1. 获取账号总数和所有账号信息
        user_count_cloudTrader = var_manager.get_variable("user_count_cloudTrader", 0)
        if user_count_cloudTrader < 0:
            pytest.fail("未找到需要验证的账号数量，请检查前置步骤")
        # 2. 初始化ID列表和计数器
        all_count_cloudTrader_ids = []
        addcloudtrader_count = 0
        # 3. 提取后6个账号（对应user_accounts_cloudTrader_5到user_accounts_cloudTrader_10）
        for i in range(5, user_count_cloudTrader + 1):
            with allure.step(f"1. 获取第{i}个跟单账号的account是否新增成功"):
                usr_account = var_manager.get_variable(f"user_accounts_cloudTrader_{i}")
                if not usr_account:
                    pytest.fail(f"第{i}个跟单账号的account为空")

                db_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM follow_cloud_trader WHERE account = %s",
                    (usr_account,),
                )
                print(f"获取第{i}个跟单账号的account:user_accounts_cloudTrader_{i}")

                if not db_data:
                    pytest.fail("数据库查询结果为空，新增云策略跟单账号失败")

                usr_account_id = db_data[0]['id']
                all_count_cloudTrader_ids.append(usr_account_id)
                var_manager.set_runtime_variable(f"traderList_cloudTrader_{i}", usr_account_id)
                logging.info(f"新增云策略跟单账号id是：traderList_cloudTrader_{i}")
        # 4.保存总数量（供后续步骤使用）
        addcloudtrader_count = len(all_count_cloudTrader_ids)
        var_manager.set_runtime_variable("addcloudtrader_count", addcloudtrader_count)
        var_manager.set_runtime_variable("all_count_cloudTrader_ids", all_count_cloudTrader_ids)
        print(f"后6个账号数据库校验完成，共提取{addcloudtrader_count}个ID，已保存到变量 all_count_cloudTrader_ids")

    # ---------------------------
    # 修改跟单账号-参数化测试（仅使用后6个数据）
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("修改跟单账号（仅使用后6个数据与模板匹配）")
    def test_update_addSlave(self, var_manager, logged_session, db_transaction):
        # 1. 获取总用户数（需确保至少有7个，才能取后6个）
        user_count_cloudTrader = var_manager.get_variable("user_count_cloudTrader", 0)
        if user_count_cloudTrader < 7:
            pytest.fail(f"用户总数需至少为7，当前为{user_count_cloudTrader}，无法提取后6个数据")

        all_ids = []
        for i in range(5, user_count_cloudTrader + 1):
            addslave_id = var_manager.get_variable(f"traderList_cloudTrader_{i}")
            if not addslave_id:
                pytest.fail(f"未找到第{i}个账号（变量：traderList_cloudTrader_{i}）")
            all_ids.append(addslave_id)
        print(f"已提取后6个账号id：{all_ids}")

        template_id = var_manager.get_variable("template_id")

        # 3. 定义6个模板（与账号一一对应）
        templates: List[Dict[str, Any]] = [
            {
                "followMode": 0,
                "followParam": "5.00",
                "templateId": 1,
                "remark": "云策略跟单账号测试数据",
                "Cfd": "",
                "mode_desc": "固定手数（5倍）"
            },
            {
                "followMode": 1,
                "followParam": "1",
                "templateId": template_id,
                "remark": "云策略跟单账号测试数据",
                "Cfd": "",
                "mode_desc": "修改品种（3倍）"
            },
            {
                "followMode": 2,
                "followParam": "1",
                "templateId": 1,
                "remark": "云策略跟单账号测试数据",
                "Cfd": "",
                "mode_desc": "净值比例"
            },
            {
                "followMode": 1,
                "followParam": "1",
                "templateId": 1,
                "remark": "云策略跟单账号测试数据",
                "Cfd": "@",
                "mode_desc": "修改币种，合约是100"
            },
            {
                "followMode": 1,
                "followParam": "1",
                "templateId": 1,
                "remark": "云策略跟单账号测试数据",
                "Cfd": ".p",
                "mode_desc": "修改币种，合约是100000"
            },
            {
                "followMode": 1,
                "followParam": "1",
                "templateId": 1,
                "remark": "云策略跟单账号测试数据",
                "Cfd": ".min",
                "mode_desc": "修改币种，合约是10"
            },
        ]

        # 4. 生成参数化数据（后6个账号与6个模板一一对应）
        parametrize_data = []
        for i in range(len(all_ids)):
            traderList = all_ids[i]
            template = templates[i]  # 直接一一对应（账号1→模板1，账号2→模板2，...）
            parametrize_data.append({
                "followMode": template["followMode"],
                "followParam": template["followParam"],
                "templateId": template["templateId"],
                "remark": template["remark"],  # 修改备注
                "Cfd": template["Cfd"],  # 修改Cfd参数
                "traderList": traderList,
            })
        print(f"生成{len(parametrize_data)}条参数化测试数据（后6个账号）")

        # 5. 循环执行后6个账号的修改操作
        for param in parametrize_data:
            with allure.step(f"1. 对数据进行参数化修改"):
                # 获取基础配置
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                # 构造请求数据
                data = {
                    "traderList": [
                        param["traderList"]
                    ],
                    "remark": param["remark"],
                    "followDirection": 0,
                    "followMode": param["followMode"],
                    "remainder": 0,
                    "followParam": param["followParam"],
                    "placedType": 0,
                    "templateId": param["templateId"],
                    "followStatus": 1,
                    "followOpen": 1,
                    "followClose": 1,
                    "followRep": None,
                    "fixedComment": "ceshi",
                    "commentType": None,
                    "digits": 0,
                    "cfd": param["Cfd"],
                    "forex": "",
                    "sort": 1,
                    "cloudId": cloudMaster_id
                }

                # 发送请求并验证
                response = self.send_post_request(
                    logged_session, '/mascontrol/cloudTrader/cloudBatchUpdate', json_data=data
                )

                self.assert_response_status(
                    response, 200,
                    f"账号{param['traderList']}修改失败"
                )
                self.assert_json_value(
                    response, "$.msg", "success",
                    f"账号{param['traderList']}响应异常"
                )
                time.sleep(3)
