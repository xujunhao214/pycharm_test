import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_701.commons.api_base import APITestBase

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestDeleteFollowSlave(APITestBase):
    # ---------------------------
    # 新增跟单账号-参数化测试（仅使用后3个数据）
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("新增跟单账号（仅使用后3个数据与模板匹配）")
    def test_import_addSlave(self, vps_api_session, var_manager, logged_session, db_transaction):
        # 1. 获取总用户数（需确保至少有6个，才能取后3个）
        user_count = var_manager.get_variable("user_count", 0)
        if user_count < 6:
            pytest.fail(f"用户总数需至少为6，当前为{user_count}，无法提取后3个数据")

        # 2. 仅提取后3个账号（索引3、4、5，对应user_accounts_4、5、6）
        # 注意：Python列表索引从0开始，后3个的索引是3,4,5（对应第4~6个数据）
        all_accounts = []
        for i in range(4, 7):  # 直接指定取4、5、6三个账号
            account = var_manager.get_variable(f"user_accounts_{i}")
            if not account:
                pytest.fail(f"未找到第{i}个账号（变量：user_accounts_{i}）")
            all_accounts.append(account)
        print(f"已提取后3个账号：{all_accounts}")

        # 3. 定义3个模板（与需求一致）
        templates: List[Dict[str, Any]] = [
            {
                "followMode": 1,
                "followParam": "1",
                "templateId": 1,
                "mode_desc": "固定跟单模式"
            },
            {
                "followMode": 0,
                "followParam": "5.00",
                "templateId": 1,
                "mode_desc": "倍数跟单模式（5倍）"
            },
            {
                "followMode": 1,
                "followParam": "1",
                "templateId": 41,
                "mode_desc": "修改品种"
            }
        ]

        # 4. 生成参数化数据（后3个账号与3个模板一一对应）
        parametrize_data = []
        for i in range(len(all_accounts)):
            # i=0 → 第1个账号对应第1个模板（索引0）
            # i=1 → 第2个账号对应第2个模板（索引1）
            # i=2 → 第3个账号对应第3个模板（索引2）
            account = all_accounts[i]
            template = templates[i]
            parametrize_data.append({
                "account": account,
                "followMode": template["followMode"],
                "followParam": template["followParam"],
                "templateId": template["templateId"],
                "desc": f"账号{account}-{template['mode_desc']}"
            })
        print(f"生成{len(parametrize_data)}条参数化测试数据（后3个账号）")

        # 5. 循环执行后3个账号的新增操作
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
                    "cfd": "",
                    "forex": "",
                    "abRemark": ""
                }

                # 发送请求并验证
                response = self.send_post_request(
                    vps_api_session, '/subcontrol/follow/addSlave', json_data=data
                )

                self.assert_response_status(
                    response, 200,
                    f"账号{param['account']}创建失败（模板：{param['desc']}）"
                )
                self.assert_json_value(
                    response, "$.msg", "success",
                    f"账号{param['account']}响应异常（模板：{param['desc']}）"
                )

    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-批量新增跟单账号")
    def test_dbimport_addSlave(self, var_manager, db_transaction):
        # 1. 获取总用户数（需确保至少有6个，才能取后3个）
        user_count = var_manager.get_variable("user_count", 0)
        if user_count < 6:
            pytest.fail(f"用户总数需至少为6，当前为{user_count}，无法提取后3个数据")

        # 2. 仅提取后3个账号（user_accounts_4、5、6）
        all_accounts = []
        for i in range(4, 7):  # 直接指定取4、5、6三个账号
            account = var_manager.get_variable(f"user_accounts_{i}")
            if not account:
                pytest.fail(f"未找到第{i}个账号（变量：user_accounts_{i}）")
            all_accounts.append(account)
        print(f"将校验后3个账号：{all_accounts}")

        # 3. 初始化计数器和ID列表
        all_ids = []
        addslave_count = 0

        # 4. 对后3个账号执行数据库校验
        for i, account in enumerate(all_accounts, 1):  # i从1开始（1、2、3）
            with allure.step(f"验证第{i}个账号（{account}）是否新增成功"):
                db_addslave_query = var_manager.get_variable("db_addslave_query")

                # 修正：按account查询，而不是remark（避免查到其他账号）
                db_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM {db_addslave_query['table']} WHERE account = %s",
                    (account,),  # 关键修改：使用当前account作为查询条件
                    time_field="create_time",
                    time_range_minutes=10
                )

                if not db_data:
                    pytest.fail(f"账号 {account} 在数据库中未找到记录")

                # 提取当前账号的ID
                vps_addslave_id = db_data[0]["id"]
                all_ids.append(vps_addslave_id)
                print(f"账号 {account} 的ID: {vps_addslave_id}")

                # 保存到变量管理器（格式：vps_addslave_ids_1, vps_addslave_ids_2, vps_addslave_ids_3）
                var_manager.set_runtime_variable(f"vps_addslave_ids_{i}", vps_addslave_id)
                print(f"已设置变量: vps_addslave_ids_{i}={vps_addslave_id}")

                # 验证账号状态和净值
                def verify_order_status():
                    status = db_data[0]["status"]
                    if status != 0:
                        pytest.fail(f"账号 {account} 状态status应为0（正常），实际状态为: {status}")
                    euqit = db_data[0]["euqit"]
                    if euqit == 0:
                        pytest.fail(f"账号 {account} 净值euqit应为非零，实际金额为: {euqit}")

                # 执行验证
                try:
                    verify_order_status()
                    allure.attach(f"账号 {account} 基础信息校验通过", "成功详情", allure.attachment_type.TEXT)
                except AssertionError as e:
                    allure.attach(str(e.args[0]), f"账号 {account} 基础信息校验失败", allure.attachment_type.TEXT)
                    raise

                # 验证订阅表记录
                db_data2 = self.query_database(
                    db_transaction,
                    f"SELECT * FROM {db_addslave_query['table_subscribe']} WHERE slave_account = %s",
                    (account,),
                    time_field="create_time",
                    time_range_minutes=10
                )

                if not db_data2:
                    pytest.fail(f"账号 {account} 在订阅表中未找到记录")

                slave_account = db_data2[0]["slave_account"]
                if slave_account != account:
                    pytest.fail(f"账号 {account} 新增失败，订阅表中记录的账号为: {slave_account}")

        # 5. 保存总数（后3个账号）
        addslave_count = len(all_ids)
        var_manager.set_runtime_variable("addslave_count", addslave_count)
        print(f"共提取{addslave_count}个用户数据（后3个账号）")
