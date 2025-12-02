# -*- coding: utf-8 -*-
import pytest
import sys
import os
import subprocess
import io
import json
from datetime import datetime
from report_generator import generate_simple_report
import xml.etree.ElementTree as ET


def run_vps_tests(env: str = "test"):
    # 设置标准输出为utf-8编码（解决print中文乱码）
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    current_script_path = os.path.abspath(__file__)
    project_root = os.path.dirname(current_script_path)

    # 定义目录路径
    report_dir = os.path.join(project_root, "report", "vps_results")  # allure结果目录（核心，用于生成报告）
    html_dir = os.path.join(project_root, "report", "vps_html")  # allure HTML报告目录
    markdown_report_path = os.path.join(project_root, "report", "VPS接口自动化测试报告.md")  # Markdown报告路径

    # 创建必要目录（确保目录存在，避免报错）
    os.makedirs(report_dir, exist_ok=True)
    os.makedirs(os.path.dirname("./Logs/vps_pytest.log"), exist_ok=True)  # 确保日志目录存在

    print(f"当前脚本绝对路径: {os.path.abspath(__file__)}")
    print(f"项目根目录: {project_root}")
    print(f"VPS 结果目录: {report_dir}")

    # pytest执行参数（核心：保留--alluredir，确保生成Allure结果文件）
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
        # "test_vps/test_vps_ordersendbuy.py",
        # "test_vps/test_vps_ordersendsell.py",
        # "test_vps/test_vps_orderclose.py",
        # "test_vps/test_vps_masOrderSend.py",
        # "test_vps/test_vps_masOrderClose.py",
        # "test_vps/test_vps_ordersenderror.py",
        # "test_vps/test_vpsOrder_open_level.py",
        # "test_vps/test_vps_query.py",
        # "test_vps/test_operation_query.py",
        # "test_vps/test_platform_query.py",
        # "test_vps/test_vpsfixed_annotations.py",
        "test_vps/test_create_scene.py",
        # "test_vps/test_vpsMasOrder_money_scene.py",
        "test_vps/test_delete.py",

        # 日志配置
        "--log-file=./Logs/vps_pytest.log",
        "--log-file-level=debug",
        "--log-file-format=%(levelname)-8s - %(asctime)s - [%(module)s:%(lineno)d] - %(message)s",
        "--log-file-date-format=%Y-%m-%d %H:%M:%S",
        "--log-level=debug"
    ]

    try:
        # 执行pytest（核心：生成Allure结果文件）
        exit_code = pytest.main(args)
        print(f"\nVPS pytest 执行完成，退出码: {exit_code}")
    except Exception as e:
        print(f"\nVPS pytest 执行异常: {str(e)}")
        exit_code = 1

    # 生成环境文件（可选：如不需要可删除此部分，不影响核心报告）
    markdown_abs_path = os.path.abspath(markdown_report_path)
    standard_path = markdown_abs_path.replace('\\', '/')
    markdown_file_url = f"file:///{standard_path}"
    generate_env_cmd = [
        "python", "generate_env.py",
        "--env", env,
        "--output-dir", report_dir,
        "--markdown-report-path", markdown_file_url
    ]
    try:
        result = subprocess.run(
            generate_env_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # 解码并打印环境文件生成日志
        encodings = ['utf-8', 'gbk', sys.getdefaultencoding(), 'latin-1']
        stderr_output = "无法解码的错误信息"
        for encoding in encodings:
            try:
                stderr_output = result.stderr.decode(encoding, errors='replace')
                break
            except:
                continue
        print(f"\nVPS环境文件生成输出: {stderr_output.encode('utf-8', errors='replace').decode('utf-8')}")
    except Exception as e:
        print(f"\nVPS 环境文件生成失败: {str(e)}（不影响Markdown报告生成）")

    # 生成Allure独立HTML报告（可选：如需单独查看Allure报告则保留，否则可删除）
    try:
        os.system(f"chcp 65001 >nul && allure generate {report_dir} -o {html_dir} --clean")
        print(f"\nVPS独立HTML报告: file://{os.path.abspath(html_dir)}/index.html")
    except Exception as e:
        print(f"\nVPS独立HTML报告生成失败: {str(e)}（不影响Markdown报告生成）")

    # 核心：调用简化后的Markdown报告生成函数（仅传3个必要参数）
    try:
        if os.path.exists(report_dir) and os.listdir(report_dir):
            generate_simple_report(report_dir, env, markdown_report_path)
        else:
            print(f"\n警告：Allure结果目录 {report_dir} 为空或不存在，未生成Markdown报告")
    except Exception as e:
        print(f"\nMarkdown报告生成失败: {str(e)}")

    return exit_code, report_dir


if __name__ == "__main__":
    # 支持命令行传入环境（如：python run_vps_tests.py prod 执行生产环境测试）
    env = sys.argv[1] if len(sys.argv) > 1 else "test"
    exit_code, _ = run_vps_tests(env)
    sys.exit(exit_code)
