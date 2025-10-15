from template.commons.api_base import APITestBase
import allure
import logging
import pytest
import json
import requests
import os
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.public_function.proportion_public import PublicUtils


# -------------------------- 关键：读取统一JSON并提取账号数据 --------------------------
def get_follow_accounts_from_runtime_json():
    """
    从 template/VAR/runtime_vars_cloud.json 中提取多账号数据
    返回格式：[{"account": "301392106", "pass_id": "xxx", "jeecg_rowkey": "xxx"}, ...]
    """
    # 1. 定义需要处理的账号列表（与JSON中的follow_XXX_xxx对应）
    # 可手动维护，或从JSON中自动匹配（下方有自动匹配方案）
    target_accounts = TRGET_ACCOUNTS

    # 2. 读取统一JSON文件（runtime_vars_cloud.json）
    json_file_path = os.path.join(
        os.path.dirname(__file__),  # 当前脚本目录
        "../VAR/runtime_vars_community.json"  # 相对于当前脚本的JSON路径，需根据实际项目调整
    )
    # 若当前脚本路径与VAR目录层级不同，可直接写绝对路径（如"D:/pycharm_test/template/VAR/runtime_vars_cloud.json"）

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            f.seek(0)
            runtime_data = json.load(f)  # 解析所有变量
    except FileNotFoundError:
        raise FileNotFoundError(f"统一变量文件不存在：{json_file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"统一变量文件格式错误（非JSON）：{json_file_path}")

    # 3. 动态提取每个账号的pass_id和jeecg_rowkey
    follow_account_list = []
    for account in target_accounts:
        # 拼接变量名（与JSON中的key对应）
        pass_id_key = f"follow_{account}_pass_id"
        jeecg_rowkey_key = f"follow_{account}_jeecg_rowkey"

        # 从JSON中提取值，确保变量存在
        pass_id = runtime_data.get(pass_id_key)
        jeecg_rowkey = runtime_data.get(jeecg_rowkey_key)

        if not pass_id or not jeecg_rowkey:
            raise KeyError(
                f"账号[{account}]缺少必要变量："
                f"\n- {pass_id_key} = {pass_id}"
                f"\n- {jeecg_rowkey_key} = {jeecg_rowkey}"
            )

        # 组装单个账号数据
        follow_account_list.append({
            "account": account,
            "pass_id": pass_id,
            "jeecg_rowkey": jeecg_rowkey
        })

    return follow_account_list


# -------------------------- 初始化账号数据 --------------------------
# 调用函数，从统一JSON中提取账号列表
# FOLLOW_ACCOUNT_LIST = get_follow_accounts_from_runtime_json()


# -------------------------- 测试类 --------------------------
@allure.feature("账号管理-批量解绑跟随者账号")
class Test_delete_batch(APITestBase):
    json_utils = JsonPathUtils()

    @allure.title("跟单社区前端-登录")
    def test_run_public(self, var_manager):
        """登录并获取token"""
        public_front = PublicUtils()
        public_front.test_login(var_manager)

    @allure.title("多账号批量解绑：取消订阅 + 前端解绑 + 数据库校验")
    @pytest.mark.parametrize("account_info", get_follow_accounts_from_runtime_json())  # 循环所有账号
    def test_batch_unbind(self, account_info, var_manager, logged_session, db_transaction):
        """单个账号完整解绑流程：取消订阅→前端解绑→数据库校验"""
        # 用例执行时再次读取JSON，获取最新数据
        latest_accounts = get_follow_accounts_from_runtime_json()
        # 从最新列表中找到当前账号的最新信息（根据account匹配）
        current_account = account_info["account"]
        latest_info = next(
            (item for item in latest_accounts if item["account"] == current_account),
            None
        )
        if not latest_info:
            pytest.fail(f"当前账号 {current_account} 在最新JSON中未找到")
        account = account_info["account"]
        pass_id = account_info["pass_id"]
        jeecg_rowkey = account_info["jeecg_rowkey"]
        allure.dynamic.description(f"当前解绑账号：{account}（pass_id：{pass_id}）")

        try:
            # -------------------------- 步骤1：取消订阅（使用jeecg_rowkey） --------------------------
            with allure.step(f"1. 取消订阅（账号：{account}）"):
                params = {"id": jeecg_rowkey}
                response = self.send_delete_request(
                    logged_session,
                    '/blockchain/master-slave/deletePa',
                    params=params
                )
                # 校验响应
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    f"账号[{account}]取消订阅失败，响应：{response.text[:500]}"
                )
                allure.attach(str(params), f"{account}取消订阅参数", allure.attachment_type.TEXT)
                allure.attach(response.text, f"{account}取消订阅响应", allure.attachment_type.JSON)

            # -------------------------- 步骤2：前端-跟单账号解绑（使用pass_id） --------------------------
            with allure.step(f"2. 前端解绑跟单账号（账号：{account}）"):
                # 从var_manager或统一JSON中获取token_top（二选一）
                # 方案1：从var_manager获取（若test_run_public登录后存入）
                token_top = var_manager.get_variable("token_top")
                # 方案2：直接从runtime_vars_cloud.json读取（若已提前存入）
                # with open("../VAR/runtime_vars_cloud.json", 'r') as f:
                #     token_top = json.load(f)["token_top"]

                assert token_top, "未获取到前端token（token_top）"

                # 构造请求
                URL_TOP = var_manager.get_variable("URL_TOP")
                Host = var_manager.get_variable("Hosttop")
                url = f"{URL_TOP}/blockchain/account/unbind?traderId={pass_id}"
                payload = json.dumps({})
                headers = {
                    'priority': 'u=1, i',
                    'x-access-token': token_top,
                    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
                    'content-type': 'application/json',
                    'Accept': '*/*',
                    'Host': Host,
                    'Connection': 'keep-alive'
                }

                # 发送请求
                response = requests.request("POST", url, headers=headers, data=payload)
                # 校验响应
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    f"账号[{account}]前端解绑失败，响应：{response.text[:500]}"
                )
                allure.attach(url, f"{account}解绑URL", allure.attachment_type.TEXT)
                allure.attach(json.dumps(headers), f"{account}解绑请求头", allure.attachment_type.JSON)
                allure.attach(response.text, f"{account}解绑响应", allure.attachment_type.JSON)

            # with allure.step(f"2. 后端解绑跟单账号（账号：{account}）"):
            #     params = {
            #         "traderId": pass_id
            #     }
            #     response = self.send_post_request(
            #         logged_session,
            #         '/blockchain/account/unbindPa',
            #         params=params
            #     )
            #
            #     self.assert_json_value(
            #         response,
            #         "$.success",
            #         True,
            #         "响应success字段应为true"
            #     )

            # -------------------------- 步骤3：数据库校验-账号状态为UNBIND --------------------------
            with allure.step(f"3. 数据库校验（账号：{account}）"):
                # 修正SQL语法：ORDER BY应在LIMIT之前
                sql = """
                    SELECT status 
                    FROM bchain_trader 
                    WHERE id = %s 
                """
                db_data = self.query_database(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=(pass_id,)
                )

                # 校验结果
                assert len(db_data) > 0, f"数据库未查询到账号[{account}]（pass_id：{pass_id}）"
                actual_status = db_data[0]["status"]
                assert actual_status == "UNBIND", \
                    f"账号[{account}]解绑状态异常：实际={actual_status}，期望=UNBIND"

                logging.info(f"账号[{account}]解绑完成，数据库状态校验通过")

        except Exception as e:
            # 异常捕获与报告
            error_msg = f"账号[{account}]解绑失败：{str(e)[:500]}"
            logging.error(error_msg, exc_info=True)
            allure.attach(error_msg, f"{account}解绑失败详情", allure.attachment_type.TEXT)
            pytest.fail(error_msg)
