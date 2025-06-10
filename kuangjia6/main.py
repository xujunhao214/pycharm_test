import os
import pytest
import logging
from typing import List


# 配置日志（替代pytest.ini中的log相关配置）
def configure_logging():
    """配置日志格式，替代pytest.ini中的log设置"""
    log_dir = "./logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "pytest.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)-8s %(asctime)s [%(name)s;%(lineno)s]  : %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )


# 定义pytest运行参数（替代pytest.ini中的addopts和markers）
def get_pytest_args() -> List[str]:
    """获取pytest运行参数，替代pytest.ini中的配置"""
    args = [
        "-vs",  # 显示详细输出和用例名称
        "./tests/test_api.py",  # 测试用例路径
        "--alluredir=./.allure_results",  # Allure报告数据目录
        "--clean-alluredir",  # 清理旧报告数据
        "--log-level=info",  # 日志级别
        "--log-format=%(levelname)-8s %(asctime)s [%(name)s;%(lineno)s]  : %(message)s",
        "--log-date-format=%Y-%m-%d %H:%M:%S",
        "--markers"  # 显示标记说明（可选）
    ]
    return args


# 主函数
if __name__ == "__main__":
    # 配置日志
    configure_logging()

    # 运行pytest
    pytest_args = get_pytest_args()
    print(f"执行pytest参数: {' '.join(pytest_args)}")
    pytest_exit_code = pytest.main(pytest_args)

    # 生成Allure报告
    if pytest_exit_code == 0:
        print("测试执行成功，生成Allure报告...")
    else:
        print(f"测试执行失败（退出码: {pytest_exit_code}），仍生成Allure报告...")

    # 执行Allure命令（建议使用subprocess替代os.system）
    import subprocess

    try:
        subprocess.run(
            "allure generate -o report .allure_results --clean",
            shell=True, check=True, capture_output=True, text=True
        )
        print("Allure报告生成成功，路径: ./report")
    except subprocess.CalledProcessError as e:
        print(f"Allure报告生成失败: {e.stderr}")
        exit(e.returncode)
