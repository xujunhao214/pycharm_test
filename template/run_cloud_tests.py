import sys
import os
import pytest
import subprocess
import io

# 获取当前脚本绝对路径和项目根目录
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(current_script_path)
# 将项目根目录加入Python搜索路径（确保能找到template_model包）
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"[路径配置] 已将项目根目录加入Python路径：{project_root}")
else:
    print(f"[路径配置] 项目根目录已在Python路径中：{project_root}")


def run_cloud_tests(env: str = "test"):
    # 解决中文乱码问题
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    # 定义报告目录（绝对路径，避免Jenkins路径混乱）
    report_dir = os.path.join(project_root, "report", "cloud_results")  # Allure结果目录（.json文件）
    html_dir = os.path.join(project_root, "report", "cloud_html")  # HTML报告目录
    # 确保目录存在（避免生成报告时目录缺失）
    os.makedirs(report_dir, exist_ok=True)
    os.makedirs(html_dir, exist_ok=True)

    # 打印关键路径信息（便于Jenkins日志排查）
    print("\n" + "=" * 50)
    print(f"[环境信息] 当前脚本绝对路径：{current_script_path}")
    print(f"[环境信息] 项目根目录：{project_root}")
    print(f"[环境信息] Allure结果目录：{report_dir}")
    print(f"[环境信息] HTML报告目录：{html_dir}")
    print(f"[环境信息] 测试环境：{env}")
    print("=" * 50 + "\n")

    # pytest执行参数（--alluredir指向结果目录，确保生成Allure数据）
    pytest_args = [
        "-s", "-v",  # 显示详细日志和打印输出
        f"--env={env}",
        f"--test-group=cloud",
        f"--alluredir={report_dir}",  # Allure核心参数：结果输出路径
        "--clean-alluredir",  # 每次执行前清空旧结果（避免脏数据）

        # 测试用例文件（基于项目根目录的相对路径，已配置路径可直接找到）
        "test_cloudTrader/test_create.py",
        "test_cloudTrader/test_agent.py",
        "test_cloudTrader/test_delete.py",
        # "test_cloudTrader/test_lianxi.py",  # 按需启用

        # 日志配置（输出到项目内Logs目录，便于追溯）
        "--log-file=./Logs/cloud_pytest.log",
        "--log-file-level=info",
        "--log-file-format=%(levelname)-8s %(asctime)s [%(name)s;%(lineno)s]  : %(message)s",
        "--log-file-date-format=%Y-%m-%d %H:%M:%S",
        "--log-level=info"
    ]

    # 执行pytest测试（捕获异常，避免脚本崩溃）
    pytest_exit_code = 1
    try:
        print(f"[pytest执行] 开始执行测试，参数：{pytest_args}")
        pytest_exit_code = pytest.main(pytest_args)
        print(f"[pytest执行] 测试完成，退出码：{pytest_exit_code}")
    except Exception as e:
        error_msg = f"[pytest执行] 执行异常：{str(e)}"
        print(f"[ERROR] {error_msg}")
        # 写入日志（可选，便于后续排查）
        with open("./Logs/cloud_pytest.log", "a", encoding="utf-8") as f:
            f.write(f"{error_msg}\n")
        pytest_exit_code = 1

    # 生成Allure环境信息文件（兼容原有逻辑）
    generate_env_cmd = [
        sys.executable,  # 使用当前Python解释器（避免环境不一致）
        os.path.join(project_root, "generate_env.py"),
        "--env", env,
        "--output-dir", report_dir
    ]
    try:
        print(f"[环境文件] 生成Allure环境信息，命令：{generate_env_cmd}")
        env_result = subprocess.run(
            generate_env_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        if env_result.stdout:
            print(f"[环境文件] 生成输出：{env_result.stdout.strip()}")
        if env_result.stderr:
            print(f"[环境文件] 警告信息：{env_result.stderr.strip()}")
    except Exception as e:
        print(f"[WARNING] 环境文件生成失败（不影响核心报告）：{str(e)}")

    # 生成Allure HTML报告（增强日志，便于定位失败原因）
    try:
        allure_cmd = f"allure generate {report_dir} -o {html_dir} --clean"
        print(f"[Allure报告] 执行生成命令：{allure_cmd}")
        # 用subprocess捕获完整输出（替代os.system，便于排查错误）
        allure_result = subprocess.run(
            allure_cmd,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        # 赋予HTML目录权限（确保Jenkins能访问）
        os.system(f"chmod -R 755 {html_dir}")
        print(f"[Allure报告] 生成成功！日志：{allure_result.stdout.strip()}")
        print(f"[Allure报告] 本地访问路径：file://{os.path.abspath(html_dir)}/index.html")
    except subprocess.CalledProcessError as e:
        # 详细打印错误信息（如allure未安装、结果目录空）
        print(f"[ERROR] Allure报告生成失败！")
        print(f"[ERROR] 执行命令：{e.cmd}")
        print(f"[ERROR] 标准输出：{e.stdout.strip()}")
        print(f"[ERROR] 错误输出：{e.stderr.strip()}")
    except Exception as e:
        print(f"[ERROR] Allure报告生成异常：{str(e)}")

    # 返回最终退出码（Jenkins根据此码判断构建结果）
    print(f"\n[执行完成] Cloud测试最终退出码：{pytest_exit_code}")
    return pytest_exit_code, report_dir


if __name__ == "__main__":
    # 接收命令行参数：第一个参数为测试环境（默认uat）
    env = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].strip() else "uat"
    exit_code, _ = run_cloud_tests(env)
    sys.exit(exit_code)
