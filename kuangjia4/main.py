import pytest
import os
import sys
from datetime import datetime


def run_tests():
    """执行测试并生成报告"""
    # 测试结果目录
    results_dir = ".allure_results"
    report_dir = "report"

    # 确保结果目录存在
    os.makedirs(results_dir, exist_ok=True)

    # 配置pytest参数
    pytest_args = [
        "-vs",  # 详细输出并显示标准输出
        "tests/test_api.py",  # 测试文件路径（修正了原有的路径问题）
        "--alluredir", results_dir,  # 指定Allure结果目录
        "--clean-alluredir",  # 执行前清理旧结果
        "--html", f"{report_dir}/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",  # 生成HTML报告
        "--self-contained-html",  # HTML报告包含所有资源
    ]

    # 添加环境选项（如果有）
    if "--env" in sys.argv:
        env_index = sys.argv.index("--env")
        if env_index + 1 < len(sys.argv):
            pytest_args.extend(["--env", sys.argv[env_index + 1]])

    # 执行pytest测试
    print(f"\n🚀 开始执行测试: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 pytest 参数: {' '.join(pytest_args)}")

    exit_code = pytest.main(pytest_args)

    # 测试结果判断
    if exit_code == 0:
        print(f"\n🎉 测试执行成功，开始生成Allure报告...")

        # 生成Allure报告
        allure_cmd = f"allure generate {results_dir} -o {report_dir}/allure --clean"
        print(f"📊 执行命令: {allure_cmd}")
        os.system(allure_cmd)

        print(f"\n✅ 测试报告已生成: {os.path.abspath(f'{report_dir}/allure/index.html')}")
    else:
        print(f"\n❌ 测试执行失败，错误码: {exit_code}")

    return exit_code


if __name__ == "__main__":
    sys.exit(run_tests())
