import pytest
import sys
import os
from datetime import datetime


def run_tests(env: str = "test"):
    # 构建pytest参数
    args = [
        "-s",  # 显示标准输出
        "-v",  # 详细输出
        f"--env={env}",  # 指定环境
        f"--alluredir=/www/python/jenkins/workspace/Documentatio_Test/results",  # allure结果目录
        "--clean-alluredir",  # 清理旧结果
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_foundation/test_create.py",  # 测试用例目录
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_foundation/test_vps_ordersend.py",  # 测试用例目录
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_foundation/test_vps_Leakage_level.py",  # 测试用例目录
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_foundation/test_vps_Leakage_open.py",  # 测试用例目录
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_foundation/test_masOrderSend_allocation.py",
        # 测试用例目录
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_foundation/test_masOrderSend_copy.py",  # 测试用例目录
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_foundation/test_create_scene.py",  # 测试用例目录
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_foundation/test_vps_scene.py",  # 测试用例目录
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_foundation/test_vps_money.py",  # 测试用例目录
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_foundation/test_delete.py",  # 测试用例目录
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_foundation/test_delete_scene.py",  # 测试用例目录
        "--log-file=./Logs/pytest.log",
        "--log-file-level=info",
        "--log-file-format=%(levelname)-8s %(asctime)s [%(name)s;%(lineno)s]  : %(message)s",
        "--log-file-date-format=%Y-%m-%d %H:%M:%S",
        "--log-level=info"
    ]

    # 执行测试
    exit_code = pytest.main(args)
    os.system('allure generate report/results -o /www/python/jenkins/workspace/Documentatio_Test/results/html --clean')

    return exit_code


if __name__ == "__main__":
    # 默认使用测试环境，可通过命令行参数指定
    env = sys.argv[1] if len(sys.argv) > 1 else "test"
    sys.exit(run_tests(env))
