# lingkuan_707/tests/test_create.py
import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_707.VAR.VAR import *
from lingkuan_707.conftest import var_manager
from lingkuan_707.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("账号管理-创建跟单账号")
class TestCreate_Scene(APITestBase):
    # ---------------------------
    # 新增跟单账号-参数化测试（仅使用后6个数据）
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("新增跟单账号（仅使用后6个数据与模板匹配）")
    def test_import_addSlave(self, var_manager, logged_session, db_transaction):
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
        template_id2 = var_manager.get_variable("template_id2")

        # 3. 定义6个模板（与账号一一对应）
        templates: List[Dict[str, Any]] = [
            {
                "followMode": 0,
                "followParam": "5.00",
                "templateId": 1,
                "Cfd": "",
                "mode_desc": "固定手数（5倍）"
            },
            {
                "followMode": 1,
                "followParam": "1",
                "templateId": template_id2,
                "Cfd": "",
                "mode_desc": "修改品种（3倍）"
            },
            {
                "followMode": 2,
                "followParam": "1",
                "templateId": 1,
                "Cfd": "",
                "mode_desc": "净值比例"
            },
            {
                "followMode": 1,
                "followParam": "1",
                "templateId": 1,
                "Cfd": "@",
                "mode_desc": "修改币种"
            },
            {
                "followMode": 1,
                "followParam": "1",
                "templateId": 1,
                "Cfd": ".p",
                "mode_desc": "修改币种"
            },
            {
                "followMode": 1,
                "followParam": "1",
                "templateId": 1,
                "Cfd": ".min",
                "mode_desc": "修改币种"
            },
        ]

        # 4. 生成参数化数据（后6个账号与6个模板一一对应）
        parametrize_data = []
        for i in range(len(all_accounts)):
            account = all_accounts[i]
            template = templates[i]  # 直接一一对应（账号1→模板1，账号2→模板2，...）
            parametrize_data.append({
                "account": account,
                "followMode": template["followMode"],
                "followParam": template["followParam"],
                "templateId": template["templateId"],
                "Cfd": template["Cfd"],  # 新增Cfd参数
                "desc": f"账号{account}-{template['mode_desc']}"
            })
        print(f"生成{len(parametrize_data)}条参数化测试数据（后6个账号）")

        # 5. 循环执行后6个账号的新增操作
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
                    "remark": param["desc"],  # 备注包含模板信息
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
                    "abRemark": ""
                }

                # 发送请求并验证
                response = self.send_post_request(
                    logged_session, '/subcontrol/follow/addSlave', json_data=data
                )

                self.assert_response_status(
                    response, 200,
                    f"账号{param['account']}创建失败（模板：{param['desc']}）"
                )
                self.assert_json_value(
                    response, "$.msg", "success",
                    f"账号{param['account']}响应异常（模板：{param['desc']}）"
                )
                time.sleep(30)

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-批量新增跟单账号")
    def test_dbimport_addSlave(self, var_manager, db_transaction):
        # 1. 校验总用户数（需至少7个，才能取后6个）
        user_count = var_manager.get_variable("user_count", 0)
        if user_count < 7:
            pytest.fail(f"用户总数需至少为7，当前为{user_count}，无法提取后6个数据进行校验")

        # 2. 提取后6个账号（对应user_accounts_2到user_accounts_7）
        all_accounts = []
        for i in range(2, 8):  # 直接指定取第2到第7个账号（共6个）
            account = var_manager.get_variable(f"user_accounts_{i}")
            if not account:
                pytest.fail(f"未找到第{i}个账号（变量：user_accounts_{i}）")
            all_accounts.append(account)
        print(f"将校验的后6个账号：{all_accounts}")

        # 3. 初始化ID列表和计数器
        all_ids = []
        addslave_count = 0

        # 4. 逐个校验后6个账号的数据库记录
        for idx, account in enumerate(all_accounts, 1):  # idx从1开始（1-6，对应6个账号）
            with allure.step(f"验证第{idx}个账号（{account}）的数据库记录"):
                db_addslave_query = var_manager.get_variable("db_addslave_query")
                if not db_addslave_query or "table" not in db_addslave_query:
                    pytest.fail("数据库查询配置不完整（缺少table信息）")

                # 按账号查询主表记录（精确匹配当前账号）
                db_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM {db_addslave_query['table']} WHERE account = %s",
                    (account,),
                    time_field="create_time",
                    time_range_minutes=10  # 限定时间范围，避免查到历史数据
                )

                if not db_data:
                    pytest.fail(f"账号 {account} 在主表中未找到记录，请检查新增是否成功")

                # 提取当前账号的ID并保存到变量管理器
                vps_addslave_id = db_data[0]["id"]
                all_ids.append(vps_addslave_id)
                var_manager.set_runtime_variable(f"vps_addslave_ids_{idx}", vps_addslave_id)
                print(f"账号 {account} 的ID为：{vps_addslave_id}，已保存到变量 vps_addslave_ids_{idx}")

                # 校验账号状态和净值（核心业务规则）
                def verify_core_fields():
                    # 校验状态（0为正常）
                    status = db_data[0]["status"]
                    if status != 0:
                        pytest.fail(f"账号 {account} 状态异常：预期status=0（正常），实际={status}")
                    # 校验净值（非零）
                    euqit = db_data[0]["euqit"]
                    if euqit == 0:
                        pytest.fail(f"账号 {account} 净值异常：预期euqit≠0，实际={euqit}")

                # 执行核心校验并记录结果
                try:
                    verify_core_fields()
                    allure.attach(f"账号 {account} 主表字段校验通过", "校验结果", allure.attachment_type.TEXT)
                except AssertionError as e:
                    allure.attach(str(e), f"账号 {account} 主表字段校验失败", allure.attachment_type.TEXT)
                    raise

                # 校验订阅表记录（从表关联）
                if "table_subscribe" in db_addslave_query:
                    db_sub_data = self.query_database(
                        db_transaction,
                        f"SELECT * FROM {db_addslave_query['table_subscribe']} WHERE slave_account = %s",
                        (account,),
                        time_field="create_time",
                        time_range_minutes=10
                    )
                    if not db_sub_data:
                        pytest.fail(f"账号 {account} 在订阅表中未找到关联记录")
                    # 校验订阅表中的账号与当前账号一致
                    slave_account = db_sub_data[0]["slave_account"]
                    if slave_account != account:
                        pytest.fail(f"订阅表账号不匹配：预期={account}，实际={slave_account}")
                    allure.attach(f"账号 {account} 订阅表关联校验通过", "校验结果", allure.attachment_type.TEXT)

        # 5. 保存总数量（供后续步骤使用）
        addslave_count = len(all_ids)
        var_manager.set_runtime_variable("addslave_count", addslave_count)
        print(f"后6个账号数据库校验完成，共提取{addslave_count}个ID，已保存到变量 addslave_count")
        time.sleep(30)

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
                    time.sleep(30)
