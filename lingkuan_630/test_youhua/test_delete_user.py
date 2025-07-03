# test_youhua/test_delete_user.py
import pytest
import allure
import time
from lingkuan_630.commons.variable_manager import VariableManager


def pytest_generate_tests(metafunc):
    """pytest钩子函数：动态生成测试用例"""
    if "user_id" in metafunc.fixturenames:
        var_manager = VariableManager()
        user_ids = var_manager.get_variable_list("user_ids", [])
        if not user_ids:
            pytest.skip("未获取到用户ID，跳过测试")
        metafunc.parametrize("user_id", user_ids)


class TestDelete:
    """删除账号测试类"""

    @allure.title("删除账号-用户ID: {user_id}")
    def test_delete_account(self, api_session, logged_session, db_transaction, user_id):
        """删除单个账号的测试逻辑（带重试机制）"""
        allure.dynamic.title(f"删除账号-用户ID: {user_id}")

        max_retries = 3
        retry_count = 0
        last_exception = None

        while retry_count < max_retries:
            retry_count += 1
            try:
                # 发送删除请求
                response = self.send_delete_request(
                    api_session,
                    "/mascontrol/user",
                    json_data=[user_id]
                )

                # 验证响应状态码
                assert response.status_code == 200, f"删除用户失败，用户ID: {user_id}, 状态码: {response.status_code}"

                # 验证JSON响应
                json_response = response.json()
                assert json_response.get(
                    "msg") == "success", f"响应msg字段应为success，用户ID: {user_id}, 实际: {json_response.get('msg')}"

                # 存储已删除账号信息
                var_manager = VariableManager()
                var_manager.append_to_list("deleted_users", {
                    "user_id": user_id,
                    "account": var_manager.get_variable(f"account_mapping.{user_id}", f"未知账号_{user_id}")
                })

                # 记录成功日志
                allure.attach(f"用户ID: {user_id} 删除成功", "测试结果")
                break

            except AssertionError as e:
                last_exception = e
                if "服务器异常，请稍后再试" in str(e):
                    # 服务器异常时使用指数退避策略重试
                    wait_time = 2 ** retry_count
                    allure.attach(
                        f"第{retry_count}次重试，等待{wait_time}秒\n错误信息: {str(e)}",
                        "重试信息"
                    )
                    time.sleep(wait_time)
                else:
                    # 非服务器异常直接抛出
                    raise e

        if retry_count >= max_retries:
            # 所有重试失败，抛出最后一次异常并附加重试信息
            error_msg = f"用户ID: {user_id} 删除失败，经过{max_retries}次重试仍未成功\n最后一次错误: {str(last_exception)}"
            allure.attach(error_msg, "最终错误")
            raise AssertionError(error_msg) from last_exception

    def send_delete_request(self, api_session, url, json_data):
        """发送删除请求的类方法（添加请求编号）"""
        request_id = f"REQ-{int(time.time() * 1000) % 10000}"
        print(f"[{request_id}] 发送删除请求，URL: {url}, 用户ID: {json_data}")
        return api_session.post(url, json=json_data)