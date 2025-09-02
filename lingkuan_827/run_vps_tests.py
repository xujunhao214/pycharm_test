import pytest
import sys
import os
import io
import subprocess

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def run_vps_tests(env: str = "test"):
    """运行VPS测试，生成独立报告，同时暴露结果目录供合并"""
    # 配置独立报告路径
    report_dir = f"report/vps_allure-results"
    html_dir = f"report/vps_html-report"
    brief_dir = f"report/vps_brief-report"

    os.makedirs(report_dir, exist_ok=True)

    # 构建pytest参数
    args = [
        "-s", "-v",
        f"--env={env}",
        f"--test-group=vps",
        f"--alluredir={report_dir}",
        "--clean-alluredir",

        "test_vps/test_create.py",
        # "test_vps/test_lianxi.py",
        # "test_vps/test_lianxi2.py",
        # "test_vps/test_getAccountDataPage.py",
        "test_vps/test_vps_ordersend.py",
        # "test_vps/test_vps_orderclose.py",
        # "test_vps/test_vps_masOrderSend.py",
        # "test_vps/test_vps_masOrderClose.py",
        # "test_vps/test_vpsOrder_open_level.py",
        # "test_vps/test_vpsfixed_annotations.py",
        "test_vps/test_create_scene.py",
        "test_vps/test_vpsMasOrder_money_scene.py",
        "test_vps/test_delete.py",

        "-o", "log_file_encoding=utf-8",
        "-o", "console_output_encoding=utf-8",

        "--log-file=./Logs/vps_pytest.log",
        "--log-file-level=info",
        "--log-file-format=%(levelname)-8s %(asctime)s [%(name)s;%(lineno)s]  : %(message)s",
        "--log-file-date-format=%Y-%m-%d %H:%M:%S",
        "--log-level=info"
    ]

    # 执行测试
    exit_code = pytest.main(args)

    # 生成环境文件
    generate_env_cmd = [
        "python", "generate_env.py",
        "--env", env, "--output-dir", report_dir
    ]
    result = subprocess.run(
        generate_env_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    print(f"VPS文件生成输出: {result.stderr}")

    # 生成独立HTML报告
    try:
        if exit_code != 0:
            os.system(f"allure generate {report_dir} -o {html_dir} --clean")
            print(f"VPS独立报告: file://{os.path.abspath(html_dir)}/index.html")
        else:
            os.system(f"allure generate {report_dir} -o {brief_dir} --clean --report-type=brief")
            print(f"VPS独立简要报告: file://{os.path.abspath(brief_dir)}/index.html")
    except Exception as e:
        print(f"VPS独立报告生成失败: {str(e)}")

    # 返回结果目录（供并行脚本合并）
    return exit_code, report_dir


if __name__ == "__main__":
    env = sys.argv[1] if len(sys.argv) > 1 else "uat"
    exit_code, _ = run_vps_tests(env)
    sys.exit(exit_code)
