import time
import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuanMT5_1029.VAR.VAR import *
from lingkuanMT5_1029.commons.jsonpath_utils import *
from lingkuanMT5_1029.conftest import var_manager
from lingkuanMT5_1029.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("云策略-云策略列表-批量新增云跟单账号")
class TestCreate_importMT5cloudTrader(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-批量新增云跟单账号")
    def test_create_importcloudBatchAdd(self, class_random_str, var_manager, logged_session):
        # 1. 获取账号总数和所有ID
        cloudMaster_id = var_manager.get_variable("cloudMaster_id")
        MT5cloudTrader_account = var_manager.get_variable("MT5cloudTrader_account", 0)
        MT5cloudTrader_traderList_2 = var_manager.get_variable("MT5cloudTrader_traderList_2")
        MT5cloudTrader_user_accounts_2 = var_manager.get_variable("MT5cloudTrader_user_accounts_2")
        if MT5cloudTrader_account < 0:
            pytest.fail("未找到需要新增的账号数量，请检查前置步骤")
        # 2. 循环获取每个账号的ID
        for i in range(4, MT5cloudTrader_account + 1):
            with (allure.step(f"1. 获取第{i}个跟单账号的ID")):
                slave_id = var_manager.get_variable(f"MT5cloudTrader_MT5vps_ids_{i}")
                if not slave_id:
                    pytest.fail(f"第{i}个跟单账号的ID为空")
                print(f"获取第{i}个跟单账号的ID:MT5cloudTrader_MT5vps_ids_{i}")
                # 3. 发送新增跟单云策略请求（接口支持单个ID删除，参数为列表形式）
                data = [
                    {
                        "traderList": [
                            slave_id
                        ],
                        "cloudId": cloudMaster_id,
                        "masterId": MT5cloudTrader_traderList_2,
                        "masterAccount": MT5cloudTrader_user_accounts_2,
                        "platformType": 1,
                        "followDirection": 1,
                        "followMode": 1,
                        "followParam": 1,
                        "remainder": 0,
                        "placedType": 0,
                        "templateId": 1,
                        "followStatus": 1,
                        "followOpen": 1,
                        "followClose": 1,
                        "fixedComment": "",
                        "remark": "",
                        "commentType": "",
                        "digits": 0,
                        "followTraderIds": [],
                        "sort": "100"
                    }
                ]
                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudBatchAdd',
                    json_data=data
                )

                # 2. 验证响应状态码
                self.assert_response_status(
                    response,
                    200,
                    "新增云跟单账号失败"
                )

                # 3. 验证JSON返回内容
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-批量新增云跟单账号")
    def test_dbquery_cloudBatchAdd(self, class_random_str, var_manager, db_transaction):
        # 1. 获取账号总数和所有账号信息
        MT5cloudTrader_user_count = var_manager.get_variable("MT5cloudTrader_user_count", 0)
        if MT5cloudTrader_user_count < 0:
            pytest.fail("未找到需要验证的账号数量，请检查前置步骤")
        # 2. 初始化ID列表和计数器
        MT5cloudTrader_all_count_ids = []
        MT5cloudTrader_add_count = 0
        # 3. 提取后6个账号（对应MT5cloudTrader_user_accounts_5到MT5cloudTrader_user_accounts_10）
        for i in range(5, MT5cloudTrader_user_count + 1):
            with allure.step(f"1. 获取第{i}个跟单账号的account是否新增成功"):
                usr_account = var_manager.get_variable(f"MT5cloudTrader_user_accounts_{i}")
                if not usr_account:
                    pytest.fail(f"第{i}个跟单账号的account为空")

                db_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM follow_cloud_trader WHERE account = %s",
                    (usr_account,),
                    order_by="account ASC"
                )
                print(f"获取第{i}个跟单账号的account:MT5cloudTrader_user_accounts_{i}")

                if not db_data:
                    pytest.fail("数据库查询结果为空，新增云跟单账号失败")

                usr_account_id = db_data[0]['id']
                MT5cloudTrader_all_count_ids.append(usr_account_id)
                var_manager.set_runtime_variable(f"MT5cloudTrader_traderList_{i}", usr_account_id)
                logging.info(f"新增云跟单账号id是：MT5cloudTrader_traderList_{i}")
        # 4.保存总数量（供后续步骤使用）
        MT5cloudTrader_add_count = len(MT5cloudTrader_all_count_ids)
        var_manager.set_runtime_variable("MT5cloudTrader_add_count", MT5cloudTrader_add_count)
        var_manager.set_runtime_variable("MT5cloudTrader_all_count_ids", MT5cloudTrader_all_count_ids)
        print(f"后6个账号数据库校验完成，共提取{MT5cloudTrader_add_count}个ID，已保存到变量 MT5cloudTrader_all_count_ids")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("修改跟单账号（仅使用后6个数据与模板匹配）")
    def test_update_addSlave(self, class_random_str, var_manager, logged_session):
        # 1. 获取总用户数（需确保至少有7个，才能取后6个）
        MT5cloudTrader_user_count = var_manager.get_variable("MT5cloudTrader_user_count", 0)
        if MT5cloudTrader_user_count < 7:
            pytest.fail(f"用户总数需至少为7，当前为{MT5cloudTrader_user_count}，无法提取后6个数据")

        all_ids = []
        for i in range(5, MT5cloudTrader_user_count + 1):
            addslave_id = var_manager.get_variable(f"MT5cloudTrader_traderList_{i}")
            if not addslave_id:
                pytest.fail(f"未找到第{i}个账号（变量：MT5cloudTrader_traderList_{i}）")
            all_ids.append(addslave_id)
        print(f"已提取后6个账号id：{all_ids}")

        MT5cloudTrader_template_id1 = var_manager.get_variable("MT5cloudTrader_template_id1")

        # 3. 定义6个模板（与账号一一对应）
        templates: List[Dict[str, Any]] = [
            {
                "followMode": 0,
                "followParam": "5.00",
                "templateId": 1,
                "remark": "云跟单账号测试数据",
                "Cfd": "",
                "mode_desc": "固定手数（5倍）"
            },
            {
                "followMode": 1,
                "followParam": "1",
                "templateId": MT5cloudTrader_template_id1,
                "remark": "云跟单账号测试数据",
                "Cfd": "",
                "mode_desc": "修改品种（3倍）"
            },
            {
                "followMode": 2,
                "followParam": "1",
                "templateId": 1,
                "remark": "云跟单账号测试数据",
                "Cfd": "",
                "mode_desc": "净值比例"
            },
            {
                "followMode": 1,
                "followParam": "1",
                "templateId": 1,
                "remark": "云跟单账号测试数据",
                "Cfd": "@",
                "mode_desc": "修改币种，合约是100"
            },
            {
                "followMode": 1,
                "followParam": "1",
                "templateId": 1,
                "remark": "云跟单账号测试数据",
                "Cfd": ".p",
                "mode_desc": "修改币种，合约是100000"
            },
            {
                "followMode": 1,
                "followParam": "1",
                "templateId": 1,
                "remark": "云跟单账号测试数据",
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
            with (allure.step(f"1. 对数据进行参数化修改")):
                # 获取基础配置
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                MT5cloudTrader_traderList_2 = var_manager.get_variable("MT5cloudTrader_traderList_2")
                MT5cloudTrader_user_accounts_2 = var_manager.get_variable("MT5cloudTrader_user_accounts_2")
                # 构造请求数据
                data = [
                    {
                        "traderList": [
                            param["traderList"]
                        ],
                        "cloudId": cloudMaster_id,
                        "masterId": MT5cloudTrader_traderList_2,
                        "masterAccount": MT5cloudTrader_user_accounts_2,
                        "followDirection": 0,
                        "followMode": param["followMode"],
                        "followParam": param["followParam"],
                        "remainder": 0,
                        "placedType": 0,
                        "templateId": param["templateId"],
                        "followStatus": 1,
                        "followOpen": 1,
                        "followClose": 1,
                        "remark": param["remark"],
                        "fixedComment": "",
                        "commentType": "",
                        "digits": 0,
                        "followTraderIds": [],
                        "sort": "100",
                        "cfd": param["Cfd"],
                        "platformType": 1,
                        "forex": ""
                    }
                ]

                # 发送请求并验证
                response = self.send_post_request(
                    logged_session, '/mascontrol/cloudTrader/cloudBatchUpdate', json_data=data
                )
                print(f"修改云跟单账号数据：{param['traderList']}")

                self.assert_response_status(
                    response, 200,
                    f"账号{param['traderList']}修改失败"
                )
                self.assert_json_value(
                    response, "$.msg", "success",
                    f"账号{param['traderList']}响应异常"
                )
