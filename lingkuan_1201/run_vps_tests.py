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

    # 核心逻辑：区分Jenkins/本地环境
    if "JENKINS_URL" in os.environ:
        # Jenkins环境：优先用BUILD_NUMBER，无则用时间戳（保留历史）
        build_id = os.environ.get("BUILD_NUMBER", datetime.now().strftime("%Y%m%d%H%M%S"))
        # 优先读取run_parallel传入的REPORT_ROOT，无则生成vps+构建号目录
        REPORT_ROOT = os.environ.get("REPORT_ROOT", os.path.join(project_root, "report", f"vps_{build_id}"))
    else:
        # 本地环境：复用固定目录（方便调试，不保留历史）
        REPORT_ROOT = os.path.join(project_root, "report")

    os.makedirs(REPORT_ROOT, exist_ok=True)  # 确保目录存在

    # 定义目录路径（全部基于REPORT_ROOT）
    report_dir = os.path.join(REPORT_ROOT, "vps_results")  # allure结果目录
    html_dir = os.path.join(REPORT_ROOT, "vps_html")  # allure HTML报告目录
    markdown_report_path = os.path.join(REPORT_ROOT, "VPS接口自动化测试报告.md")  # Markdown报告路径

    # 创建必要目录
    os.makedirs(report_dir, exist_ok=True)
    os.makedirs(os.path.dirname("./Logs/vps_pytest.log"), exist_ok=True)

    print(f"当前脚本绝对路径: {os.path.abspath(__file__)}")
    print(f"项目根目录: {project_root}")
    print(f"VPS 结果目录: {report_dir}")
    print(f"VPS 报告根目录: {REPORT_ROOT} (Jenkins环境: {'是' if 'JENKINS_URL' in os.environ else '否'})")

    # pytest执行参数
    args = [
        "-s", "-v",
        f"--env={env}",
        f"--test-group=vps",
        f"--alluredir={report_dir}",
        "--clean-alluredir",

        "test_vps/test_lianxi.py",

        # 日志配置
        "--log-file=./Logs/vps_pytest.log",
        "--log-file-level=debug",
        "--log-file-format=%(levelname)-8s - %(asctime)s - [%(module)s:%(lineno)d] - %(message)s",
        "--log-file-date-format=%Y-%m-%d %H:%M:%S",
        "--log-level=debug"
    ]

    try:
        exit_code = pytest.main(args)
        print(f"\nVPS pytest 执行完成，退出码: {exit_code}")
    except Exception as e:
        print(f"\nVPS pytest 执行异常: {str(e)}")
        exit_code = 1

    # 生成环境文件
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

    # 生成Allure独立HTML报告
    try:
        os.system(f"chcp 65001 >nul && allure generate {report_dir} -o {html_dir} --clean")
        print(f"\nVPS独立HTML报告: file://{os.path.abspath(html_dir)}/index.html")
    except Exception as e:
        print(f"\nVPS独立HTML报告生成失败: {str(e)}（不影响Markdown报告生成）")

    # 生成Markdown报告
    try:
        if os.path.exists(report_dir) and os.listdir(report_dir):
            generate_simple_report(report_dir, env, markdown_report_path)
            print(f"\n✅ VPS MD报告生成路径: {markdown_report_path}")
        else:
            print(f"\n警告：Allure结果目录 {report_dir} 为空或不存在，未生成Markdown报告")
    except Exception as e:
        print(f"\nMarkdown报告生成失败: {str(e)}")

    return exit_code, report_dir


if __name__ == "__main__":
    env = sys.argv[1] if len(sys.argv) > 1 else "uat"
    exit_code, _ = run_vps_tests(env)
    sys.exit(exit_code)