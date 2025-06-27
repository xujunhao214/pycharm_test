import pytest
import sys
import os
from datetime import datetime


def run_tests(env: str = "test"):
    """运行测试并生成报告"""
    # 创建时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 配置报告路径
    report_dir = f"report/allure-results_{timestamp}"
    html_dir = f"report/html_{timestamp}"

    # 构建pytest参数
    args = [
        "-s",  # 显示标准输出
        "-v",  # 详细输出
        f"--env={env}",  # 指定环境
        f"--alluredir={report_dir}",  # allure结果目录
        "--clean-alluredir",  # 清理旧结果
        "tests/",  # 测试用例目录
    ]

    # 执行测试
    exit_code = pytest.main(args)

    # 生成HTML报告
    if exit_code == 0:
        os.system(f"allure generate {report_dir} -o {html_dir} --clean")
        print(f"HTML报告已生成: file://{os.path.abspath(html_dir)}/index.html")

    return exit_code


if __name__ == "__main__":
    # 默认使用测试环境，可通过命令行参数指定
    env = sys.argv[1] if len(sys.argv) > 1 else "test"
    sys.exit(run_tests(env))
