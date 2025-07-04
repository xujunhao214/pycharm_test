import pytest
import sys
import os
from datetime import datetime


def run_tests(env: str = "test"):
    """运行测试并生成报告"""
    # # 创建时间戳
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    #
    # # 配置报告路径
    # report_dir = f"report/allure-results_{timestamp}"
    # html_dir = f"report/html_{timestamp}"
    # brief_dir = "report/brief-{timestamp}"
    """运行测试并生成报告（固定路径版本）"""
    """智能生成报告：失败时详细报告，通过时简要报告"""
    report_dir = "report/allure-results"
    html_dir = "report/html-report"
    brief_dir = "report/brief-report"

    # 构建pytest参数
    args = [
        "-s",  # 显示标准输出
        "-v",  # 详细输出
        f"--env={env}",  # 指定环境
        f"--alluredir={report_dir}",  # allure结果目录
        "--clean-alluredir",  # 清理旧结果
        # "test_foundation/test_create.py",  # 测试用例目录
        # "test_foundation/test_vps_ordersend.py",  # 测试用例目录
        # "test_foundation/test_vps_Leakage_level.py",  # 测试用例目录
        # "test_foundation/test_vps_Leakage_open.py",  # 测试用例目录
        # "test_foundation/test_masOrderSend_allocation.py",  # 测试用例目录
        "test_foundation/test_masOrderSend_copy.py",  # 测试用例目录
        # "test_foundation/test_lianxi.py",  # 测试用例目录
        # "test_foundation/test_lianxi2.py",  # 测试用例目录
        # "test_foundation/test_create_scene.py",  # 测试用例目录
        # "test_foundation/test_vps_scene.py",  # 测试用例目录
        # "test_foundation/test_vps_money.py",  # 测试用例目录
        # "test_foundation/test_delete.py",  # 测试用例目录
        # "test_foundation/test_delete_scene.py",  # 测试用例目录

        # "test_fusion/test_create.py",  # 测试用例目录
        # "test_fusion/test_vps.py",  # 测试用例目录
        # "test_fusion/test_masOrderSend.py",  # 测试用例目录
        # "test_fusion/test_create_scene.py",  # 测试用例目录
        # "test_fusion/test_vps_scene.py",  # 测试用例目录
        # "test_fusion/test_delete.py",  # 测试用例目录
        "--log-file=./Logs/pytest.log",
        "--log-file-level=info",
        "--log-file-format=%(levelname)-8s %(asctime)s [%(name)s;%(lineno)s]  : %(message)s",
        "--log-file-date-format=%Y-%m-%d %H:%M:%S",
        "--log-level=info"
    ]

    # 执行测试
    exit_code = pytest.main(args)

    try:
        if exit_code != 0:
            # 测试失败，生成详细报告
            os.system(f"allure generate {report_dir} -o {html_dir} --clean")
            print(f"测试失败，详细报告: file://{os.path.abspath(html_dir)}/index.html")
        else:
            # 测试通过，生成简要报告
            os.system(f"allure generate {report_dir} -o {brief_dir} --clean --report-type=brief")
            print(f"测试通过，简要报告: file://{os.path.abspath(brief_dir)}/index.html")
    except Exception as e:
        print(f"生成报告失败: {str(e)}")

    return exit_code


if __name__ == "__main__":
    # 默认使用测试环境，可通过命令行参数指定
    env = sys.argv[1] if len(sys.argv) > 1 else "prod"
    sys.exit(run_tests(env))
