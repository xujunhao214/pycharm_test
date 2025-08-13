import pytest
import sys
import os
import subprocess
from datetime import datetime


def run_tests(env: str = "test"):
    """运行测试并生成报告"""
    # 创建时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 配置报告路径
    report_dir = f"report/allure-results_{timestamp}"
    html_dir = f"report/html_{timestamp}"
    brief_dir = f"report/brief_{timestamp}"
    # """运行测试并生成报告（固定路径版本）"""
    # """智能生成报告：失败时详细报告，通过时简要报告"""
    # report_dir = "report/allure-results"
    # html_dir = "report/html-report"
    # brief_dir = "report/brief-report"

    # 定义两个目录的用例文件列表（按执行顺序排列，与Jenkins保持一致）
    test_vps_files = [
        "test_vps/test_create.py",
        # "test_vps/test_vps_ordersend.py",
        # "test_vps/test_vps_Leakage_level.py",
        # "test_vps/test_vps_Leakage_open.py",
        # "test_vps/test_masOrderSend_allocation.py",
        # "test_vps/test_masOrderSend_copy.py",
        "test_vps/test_create_scene.py",
        # "test_vps/test_vps_scene.py",
        # "test_vps/test_vps_money.py",
        "test_vps/test_delete.py",
        "test_vps/test_delete_scene.py",
        # 可选：添加lianxi等临时测试文件
        # "test_vps/test_lianxi.py",
        # "test_vps/test_lianxi2.py",
    ]

    test_cloudTrader_files = [
        "test_cloudTrader/test_create.py",
        # "test_cloudTrader/test_cloudOrderSend_allocation.py",
        # "test_cloudTrader/test_cloudOrderSend_copy.py",
        # "test_cloudTrader/test_cloudOrderSend_manageropen.py",
        # "test_cloudTrader/test_masOrderSend_cloudcopy.py",
        # "test_cloudTrader/test_cloudOrderSend_managerlevel.py",
        # "test_cloudTrader/test_cloudOrderSend_open.py",
        # "test_cloudTrader/test_cloudOrderSend_level.py",
        "test_cloudTrader/test_create_scene.py",
        # "test_cloudTrader/test_cloudtrader_scene.py",
        # "test_cloudTrader/test_cloudtrader_money.py",
        "test_cloudTrader/test_delete_scene.py",
        "test_cloudTrader/test_delete.py",
        # 可选：添加lianxi等临时测试文件
        # "test_cloudTrader/test_lianxi.py",
        # "test_cloudTrader/test_lianxi2.py",
    ]

    # 合并用例列表（两个目录并行，目录内按顺序执行）
    all_test_files = test_vps_files + test_cloudTrader_files

    # 构建pytest参数（核心：并行+顺序控制）
    args = [
        "-s",  # 显示标准输出
        "-v",  # 详细输出
        f"--env={env}",  # 指定环境
        f"--alluredir={report_dir}",  # allure结果目录
        "--clean-alluredir",  # 清理旧结果

        # 并行执行配置（与Jenkins保持一致）
        "-n", "2",  # 2个进程（分别处理两个目录，实现并行）
        "--dist=loadscope",  # 按文件分配进程：同一文件的用例在同一进程执行
        "--order-scope=module",  # 按文件顺序执行（需安装pytest-order==1.1.0）

        # 传入所有测试文件（按定义的顺序）
        *all_test_files,

        # 日志配置
        "--log-file=./Logs/pytest.log",
        "--log-file-level=info",
        "--log-file-format=%(levelname)-8s %(asctime)s [%(name)s;%(lineno)s]  : %(message)s",
        "--log-file-date-format=%Y-%m-%d %H:%M:%S",
        "--log-level=info"
    ]

    # 生成环境文件（测试前后各执行一次）
    generate_env_cmd = [
        "python", "generate_env.py",
        "--env", env,
        "--output-dir", report_dir
    ]
    # 测试前生成环境文件
    result = subprocess.run(
        generate_env_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"  # 确保中文正常显示
    )
    print(f"生成环境文件输出: {result.stdout}")
    if result.stderr:
        print(f"生成环境文件错误: {result.stderr}")

    # 执行pytest测试
    exit_code = pytest.main(args)

    # 测试后再次生成环境文件
    result = subprocess.run(
        generate_env_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )
    print(f"测试后重新生成环境文件输出: {result.stdout}")
    if result.stderr:
        print(f"测试后生成环境文件错误: {result.stderr}")

    # 生成测试报告（失败详细报告，成功简要报告）
    try:
        if exit_code != 0:
            os.system(f"allure generate {report_dir} -o {html_dir} --clean")
            print(f"测试失败，详细报告: file://{os.path.abspath(html_dir)}/index.html")
        else:
            os.system(f"allure generate {report_dir} -o {brief_dir} --clean --report-type=brief")
            print(f"测试通过，简要报告: file://{os.path.abspath(brief_dir)}/index.html")
    except Exception as e:
        print(f"生成报告失败: {str(e)}")

    return exit_code


if __name__ == "__main__":
    # 从命令行参数获取环境（默认test）
    env = sys.argv[1] if len(sys.argv) > 1 else "test"
    # 确保日志目录存在
    os.makedirs("./Logs", exist_ok=True)
    # 执行测试
    sys.exit(run_tests(env))
