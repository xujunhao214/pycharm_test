# commons/wait_utils.py
import time
import allure
from allure_commons.model2 import Status
from allure_commons.reporter import AllureReporter
from allure_commons._allure import StepContext
from typing import Callable, Any, Optional
from lingkuan_1201.VAR.VAR import *


def wait_for_condition(
        condition: Callable[[], Any],
        timeout: int = WAIT_TIMEOUT,
        poll_interval: float = POLL_INTERVAL,
        error_message: str = "等待条件超时未满足",
        step_title: Optional[str] = None
) -> Any:
    """
    智能等待条件满足，同时记录Allure步骤

    Args:
        condition: 检查条件的函数，返回结果表示条件是否满足
        timeout: 最长等待时间（秒）
        poll_interval: 轮询间隔（秒）
        error_message: 超时错误信息
        step_title: Allure步骤标题，默认为"等待条件满足"

    Returns:
        条件函数的返回值
    """
    step_title = step_title or f"等待条件满足 (超时: {timeout}秒)"

    with allure.step(step_title):
        start_time = time.time()
        elapsed_time = 0
        last_result = None

        while elapsed_time < timeout:
            try:
                last_result = condition()
                allure.attach(
                    f"轮询检查结果 (已等待 {elapsed_time:.1f}秒): {last_result}",
                    name="条件检查日志",
                    attachment_type=allure.attachment_type.TEXT
                )

                if last_result:
                    allure.attach(
                        f"条件满足，耗时: {elapsed_time:.1f}秒",
                        name="最终结果",
                        attachment_type=allure.attachment_type.TEXT
                    )
                    return last_result
            except Exception as e:
                allure.attach(
                    f"轮询异常 (已等待 {elapsed_time:.1f}秒): {str(e)}",
                    name="异常信息",
                    attachment_type=allure.attachment_type.TEXT
                )
                raise

            time.sleep(poll_interval)
            elapsed_time = time.time() - start_time

        # 超时处理
        allure.attach(
            f"等待超时 ({timeout}秒)，最终检查结果: {last_result}",
            name="超时信息",
            attachment_type=allure.attachment_type.TEXT
        )
        raise TimeoutError(error_message)
