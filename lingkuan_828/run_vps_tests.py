import pytest
import sys
import os
import subprocess


def run_vps_tests(env: str = "test"):
    # 1. 获取当前脚本的绝对路径
    current_script_path = os.path.abspath(__file__)
    # 2. 获取脚本所在的目录
    project_root = os.path.dirname(current_script_path)

    # 3. 基于项目根目录，动态生成报告路径（相对路径转绝对路径）
    report_dir = os.path.join(project_root, "report", "vps_results")
    html_dir = os.path.join(project_root, "report", "vps_html")

    os.makedirs(report_dir, exist_ok=True)

    print(f"当前脚本绝对路径: {os.path.abspath(__file__)}")
    print(f"项目根目录: {project_root}")
    print(f"VPS 结果目录: {report_dir}")

    # 构建pytest参数
    args = [
        "-s", "-v",
        f"--env={env}",
        f"--test-group=vps",
        f"--alluredir={report_dir}",
        "--clean-alluredir",

        # "test_vps/test_create.py",
        # "test_vps/test_lianxi.py",
        "test_vps/test_lianxi2.py",
        # "test_vps/test_getAccountDataPage.py",
        # "test_vps/test_vps_ordersend.py",
        # "test_vps/test_vps_orderclose.py",
        # "test_vps/test_vps_masOrderSend.py",
        # "test_vps/test_vps_masOrderClose.py",
        # "test_vps/test_vpsOrder_open_level.py",
        # "test_vps/test_vpsfixed_annotations.py",
        # "test_vps/test_create_scene.py",
        # "test_vps/test_vpsMasOrder_money_scene.py",
        # "test_vps/test_delete.py",

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
        encoding="utf-8"
    )
    print(f"VPS文件生成输出: {result.stderr}")

    # 生成独立HTML报告
    try:
        os.system(f"allure generate {report_dir} -o {html_dir} --clean")
        print(f"VPS独立报告: file://{os.path.abspath(html_dir)}/index.html")
    except Exception as e:
        print(f"VPS独立报告生成失败: {str(e)}")

    # 返回结果目录（供并行脚本合并）
    return exit_code, report_dir


if __name__ == "__main__":
    env = sys.argv[1] if len(sys.argv) > 1 else "uat"
    exit_code, _ = run_vps_tests(env)
    sys.exit(exit_code)
