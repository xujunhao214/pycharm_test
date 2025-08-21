import pytest
import sys
import os
import subprocess


def run_vps_tests(env: str = "test"):
    """运行VPS相关测试并生成报告"""
    # 配置报告路径
    report_dir = f"report/vps_allure-results"
    html_dir = f"report/vps_html-report"
    brief_dir = f"report/vps_brief-report"

    # 构建pytest参数（仅包含VPS相关测试）
    args = [
        "-s",  # 显示标准输出
        "-v",  # 详细输出
        f"--env={env}",  # 指定环境
        f"--alluredir={report_dir}",  # allure结果目录
        "--clean-alluredir",  # 清理旧结果
        "test_vps/test_create.py",
        # "test_vps/test_vps_Leakage_level.py",
        # "test_vps/test_vps_Leakage_open.py",
        # "test_vps/test_masOrderSend.py",
        # "test_vps/test_vps_ordersend.py",
        # "test_vps/test_lianxi.py",
        # "test_vps/test_lianxi2.py",
        "test_vps/test_create_scene.py",
        # "test_vps/test_vps_scene.py",
        # "test_vps/test_vps_money.py",
        "test_vps/test_delete.py",
        "test_vps/test_delete_scene.py",

        "--log-file=./Logs/vps_pytest.log",
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

    # 执行pytest测试
    exit_code = pytest.main(args)

    # 测试后生成环境文件（指定utf-8编码）
    result = subprocess.run(
        generate_env_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )
    print(f"VPS文件生成输出: {result.stderr}")

    try:
        if exit_code != 0:
            # 测试失败，生成详细报告
            os.system(f"allure generate {report_dir} -o {html_dir} --clean")
            print(f"VPS测试失败，详细报告: file://{os.path.abspath(html_dir)}/index.html")
        else:
            # 测试通过，生成简要报告
            os.system(f"allure generate {report_dir} -o {brief_dir} --clean --report-type=brief")
            print(f"VPS测试通过，简要报告: file://{os.path.abspath(brief_dir)}/index.html")
    except Exception as e:
        print(f"VPS测试报告生成失败: {str(e)}")

    return exit_code


if __name__ == "__main__":
    # 默认使用测试环境，可通过命令行参数指定
    env = sys.argv[1] if len(sys.argv) > 1 else "test"
    sys.exit(run_vps_tests(env))
