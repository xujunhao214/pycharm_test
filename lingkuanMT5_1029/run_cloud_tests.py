import pytest
import sys
import os
import subprocess
import io


def run_cloud_tests(env: str = "test"):
    # 设置标准输出为utf-8编码（解决print中文乱码）
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    current_script_path = os.path.abspath(__file__)
    project_root = os.path.dirname(current_script_path)

    report_dir = os.path.join(project_root, "report", "cloud_results")
    html_dir = os.path.join(project_root, "report", "cloud_html")
    os.makedirs(report_dir, exist_ok=True)

    print(f"当前脚本绝对路径: {os.path.abspath(__file__)}")
    print(f"项目根目录: {project_root}")
    print(f"Cloud 结果目录: {report_dir}")

    args = [
        "-s", "-v",
        f"--env={env}",
        f"--test-group=cloud",
        f"--alluredir={report_dir}",
        "--clean-alluredir",

        "test_cloudTrader/test_create.py",
        # "test_cloudTrader/test_lianxi.py",
        # "test_cloudTrader/test_lianxi2.py",
        # "test_cloudTrader/test_getAccountDataPage.py",
        "test_cloudTrader/test_cloudOrderSendbuy.py",
        "test_cloudTrader/test_cloudOrderSendsell.py",
        "test_cloudTrader/test_cloudOrderClose.py",
        "test_cloudTrader/test_cloud_masOrderSend.py",
        "test_cloudTrader/test_cloud_masOrderClose.py",
        "test_cloudTrader/test_cloudOrder_open_level.py",
        "test_cloudTrader/test_cloudfixed_annotations.py",
        "test_cloudTrader/test_create_scene.py",
        "test_cloudTrader/test_cloudTrader_money_scene.py",
        "test_cloudTrader/test_delete.py",

        "--log-file=./Logs/cloud_pytest.log",
        "--log-file-level=debug",
        "--log-file-format=%(levelname)-8s - %(asctime)s - [%(module)s:%(lineno)d] - %(message)s",
        "--log-file-date-format=%Y-%m-%d %H:%M:%S",
        "--log-level=debug"
    ]

    try:
        exit_code = pytest.main(args)
        print(f"Cloud pytest 执行完成，退出码: {exit_code}")
    except Exception as e:
        print(f"Cloud pytest 执行异常: {str(e)}")
        exit_code = 1

    # 生成环境文件（字节流处理+安全编码）
    generate_env_cmd = [
        "python", "generate_env.py",
        "--env", env, "--output-dir", report_dir
    ]
    try:
        result = subprocess.run(
            generate_env_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # 解码stderr（多编码尝试+替换错误字符）
        encodings = ['utf-8', 'gbk', sys.getdefaultencoding(), 'latin-1']
        stderr_output = "无法解码的错误信息"
        for encoding in encodings:
            try:
                stderr_output = result.stderr.decode(encoding, errors='replace')
                break
            except:
                continue

        # 打印时确保编码兼容
        print(f"Cloud文件生成输出: {stderr_output.encode('utf-8', errors='replace').decode('utf-8')}")
    except Exception as e:
        print(f"Cloud 环境文件生成失败: {str(e)}")

    try:
        os.system(f"allure generate {report_dir} -o {html_dir} --clean")
        print(f"Cloud独立报告: file://{os.path.abspath(html_dir)}/index.html")
    except Exception as e:
        print(f"Cloud独立报告生成失败: {str(e)}")

    return exit_code, report_dir


if __name__ == "__main__":
    env = sys.argv[1] if len(sys.argv) > 1 else "test"
    exit_code, _ = run_cloud_tests(env)
    sys.exit(exit_code)
