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
    report_dir = os.path.join(project_root, "report", "vps_results")  # allure结果目录
    html_dir = os.path.join(project_root, "report", "vps_html")  # allure HTML报告目录
    markdown_report_path = os.path.join(project_root, "report", "VPS接口自动化测试报告.md")  # Markdown报告路径
    os.makedirs(report_dir, exist_ok=True)

    print(f"当前脚本绝对路径: {os.path.abspath(__file__)}")
    print(f"项目根目录: {project_root}")
    print(f"VPS 结果目录: {report_dir}")

    # pytest执行参数
    args = [
        "-s", "-v",
        f"--env={env}",
        f"--test-group=vps",
        f"--alluredir={report_dir}",
        "--clean-alluredir",

        # "test_vps/test_create.py",
        "test_vps/test_lianxi.py",
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
        # "test_vps/test_history_query.py",
        # "test_vps/test_vpsfixed_annotations.py",
        # "test_vps/test_create_scene.py",
        # "test_vps/test_vpsMasOrder_money_scene.py",
        # "test_vps/test_delete.py",

        "--log-file=./Logs/vps_pytest.log",
        "--log-file-level=debug",
        "--log-file-format=%(levelname)-8s - %(asctime)s - [%(module)s:%(lineno)d] - %(message)s",
        "--log-file-date-format=%Y-%m-%d %H:%M:%S",
        "--log-level=debug"
    ]

    try:
        exit_code = pytest.main(args)
        print(f"VPS pytest 执行完成，退出码: {exit_code}")
    except Exception as e:
        print(f"VPS pytest 执行异常: {str(e)}")
        exit_code = 1

    # ========== 关键：动态生成 Markdown 报告的 file:// 路径 ==========
    markdown_abs_path = os.path.abspath(markdown_report_path)
    standard_path = markdown_abs_path.replace('\\', '/')  # 替换反斜杠，兼容Python 3.8
    markdown_file_url = f"file:///{standard_path}"  # 生成可点击的 file:// 路径

    # 生成环境文件（传入 Markdown 报告路径）
    generate_env_cmd = [
        "python", "generate_env.py",
        "--env", env,
        "--output-dir", report_dir,
        "--markdown-report-path", markdown_file_url  # 新增参数：传入可点击路径
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
        print(f"VPS文件生成输出: {stderr_output.encode('utf-8', errors='replace').decode('utf-8')}")
    except Exception as e:
        print(f"VPS 环境文件生成失败: {str(e)}")

    # 生成Allure HTML报告
    try:
        os.system(f"chcp 65001 >nul && allure generate {report_dir} -o {html_dir} --clean")
        print(f"VPS独立HTML报告: file://{os.path.abspath(html_dir)}/index.html")
    except Exception as e:
        print(f"VPS独立HTML报告生成失败: {str(e)}")

    # 调用Markdown报告生成函数
    generate_simple_report(report_dir, env, markdown_report_path)

    return exit_code, report_dir


if __name__ == "__main__":
    env = sys.argv[1] if len(sys.argv) > 1 else "test"
    exit_code, _ = run_vps_tests(env)
    sys.exit(exit_code)
