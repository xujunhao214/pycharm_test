import pytest
import sys
import os
from datetime import datetime
import subprocess


def run_tests(env: str = "test"):
    """运行测试并生成报告"""
    """运行测试并生成报告（固定路径版本）"""
    """智能生成报告：失败时详细报告，通过时简要报告"""
    report_dir = "report/results"
    html_dir = "/www/python/jenkins/workspace/Documentatio_Test/results/html"

    # 构建pytest参数
    # 构建pytest参数
    args = [
        "-s",  # 显示标准输出
        "-v",  # 详细输出
        f"--env={env}",  # 指定环境
        f"--alluredir=/www/python/jenkins/workspace/Documentatio_Test/results",  # allure结果目录
        "--clean-alluredir",  # 清理旧结果

        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_vps/test_create.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_vps/test_vps_ordersend.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_vps/test_vps_Leakage_level.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_vps/test_vps_Leakage_open.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_vps/test_masOrderSend_allocation.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_vps/test_masOrderSend_copy.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_vps/test_create_scene.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_vps/test_vps_scene.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_vps/test_vps_money.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_vps/test_delete.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_vps/test_delete_scene.py",

        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_cloudTrader/test_create.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_cloudTrader/test_cloudOrderSend_allocation.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_cloudTrader/test_cloudOrderSend_copy.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_cloudTrader/test_cloudOrderSend_manageropen.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_cloudTrader/test_masOrderSend_cloudcopy.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_cloudTrader/test_cloudOrderSend_managerlevel.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_cloudTrader/test_cloudOrderSend_open.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_cloudTrader/test_cloudOrderSend_level.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_cloudTrader/test_create_scene.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_cloudTrader/test_cloudtrader_scene.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_cloudTrader/test_cloudtrader_money.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_cloudTrader/test_delete_scene.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan/test_cloudTrader/test_delete.py",

        "--log-file=./Logs/pytest.log",
        "--log-file-level=info",
        "--log-file-format=%(levelname)-8s %(asctime)s [%(name)s;%(lineno)s]  : %(message)s",
        "--log-file-date-format=%Y-%m-%d %H:%M:%S",
        "--log-level=info"
    ]

    # 生成环境文件命令
    generate_env_cmd = [
        "python", "generate_env.py",
        "--env", env,
        "--output-dir", report_dir
    ]

    # 测试前生成环境文件（指定utf-8编码）
    result = subprocess.run(
        generate_env_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"  # 关键修改：指定utf-8编码
    )
    print(f"生成环境文件输出: {result.stdout}")
    if result.stderr:
        print(f"生成环境文件错误: {result.stderr}")

    # 执行pytest测试
    exit_code = pytest.main(args)

    # 测试后再次生成环境文件（指定utf-8编码）
    result = subprocess.run(
        generate_env_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"  # 关键修改：指定utf-8编码
    )
    print(f"测试后重新生成环境文件输出: {result.stdout}")
    if result.stderr:
        print(f"测试后生成环境文件错误: {result.stderr}")

    try:
        if exit_code != 0:
            os.system(f"allure generate {report_dir} -o {html_dir} --clean")
            print(f"测试失败，详细报告: file://{os.path.abspath(html_dir)}/index.html")
    except Exception as e:
        print(f"生成报告失败: {str(e)}")

    return exit_code


if __name__ == "__main__":
    # 默认使用测试环境，可通过命令行参数指定
    env = sys.argv[1] if len(sys.argv) > 1 else "test"
    sys.exit(run_tests(env))
