import pytest
import sys
import os
import subprocess


def run_tests(env: str = "test"):
    """运行测试并生成报告（支持目录并行+目录内按文件顺序执行）"""
    report_dir = "/www/python/jenkins/workspace/Documentatio_Test/results"
    html_dir = "/www/python/jenkins/workspace/Documentatio_Test/results/html"

    # 定义两个目录的用例文件列表（按期望的执行顺序排列）
    test_vps_files = [
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
    ]

    test_cloudTrader_files = [
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
    ]

    # 合并用例列表（两个目录的文件会并行执行，但目录内按顺序）
    all_test_files = test_vps_files + test_cloudTrader_files

    # 构建pytest参数（核心：并行+顺序控制）
    args = [
        "-s",  # 显示标准输出
        "-v",  # 详细输出
        f"--env={env}",  # 指定环境
        f"--alluredir={report_dir}",  # allure结果目录
        "--clean-alluredir",  # 清理旧结果

        # 并行执行关键参数
        "-n", "2",  # 2个进程（分别处理两个目录，实现并行）
        "--dist=loadfile",  # 按文件分配进程：同一文件的用例在同一进程执行
        "--order-scope=module",  # 按文件顺序执行（兼容 pytest-order==1.1.0）

        # 传入所有测试文件（按定义的顺序）
        *all_test_files,

        # 日志配置
        "--log-file=./Logs/pytest.log",
        "--log-file-level=info",
        "--log-file-format=%(levelname)-8s %(asctime)s [%(name)s;%(lineno)s]  : %(message)s",
        "--log-file-date-format=%Y-%m-%d %H:%M:%S",
        "--log-level=info"
    ]

    # 生成环境文件（测试前）
    generate_env_cmd = [
        "python", "generate_env.py",
        "--env", env,
        "--output-dir", report_dir
    ]
    result = subprocess.run(
        generate_env_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )
    print(f"生成环境文件输出: {result.stdout}")
    if result.stderr:
        print(f"生成环境文件错误: {result.stderr}")

    # 执行pytest测试
    exit_code = pytest.main(args)

    # 生成环境文件（测试后）
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

    # 生成测试报告
    try:
        if exit_code != 0:
            os.system(f"allure generate {report_dir} -o {html_dir} --clean")
            print(f"测试失败，详细报告: file://{os.path.abspath(html_dir)}/index.html")
    except Exception as e:
        print(f"生成报告失败: {str(e)}")

    return exit_code


if __name__ == "__main__":
    # 从命令行参数获取环境（默认test）
    env = sys.argv[1] if len(sys.argv) > 1 else "test"
    sys.exit(run_tests(env))
