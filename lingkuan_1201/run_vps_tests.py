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

    # 核心逻辑：完全复用run_parallel传递的REPORT_ROOT（统一报告目录）
    # Jenkins环境：run_parallel已传递带build_${BUILD_NUMBER}的REPORT_ROOT
    # 本地环境：兜底使用固定report目录
    REPORT_ROOT = os.environ.get("REPORT_ROOT", os.path.join(project_root, "report"))
    os.makedirs(REPORT_ROOT, exist_ok=True)  # 确保目录存在

    # 定义目录路径（全部基于REPORT_ROOT，与run_parallel完全对齐）
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
        sys.executable,  # 替换python为sys.executable，兼容多Python环境
        "generate_env.py",
        "--env", env,
        "--output-dir", report_dir,
        "--markdown-report-path", markdown_file_url
    ]
    try:
        result = subprocess.run(
            generate_env_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8"  # 直接指定编码，避免多次解码
        )
        # 合并stdout和stderr输出
        env_output = result.stdout + result.stderr
        print(f"\nVPS环境文件生成输出: {env_output}")
    except Exception as e:
        print(f"\nVPS 环境文件生成失败: {str(e)}（不影响Markdown报告生成）")

    # 生成Allure独立HTML报告（兼容Windows/Linux）
    try:
        if os.name == "nt":  # Windows系统
            os.system(f"chcp 65001 >nul && allure generate {report_dir} -o {html_dir} --clean")
        else:  # Linux/Mac系统（Jenkins）
            os.system(f"allure generate {report_dir} -o {html_dir} --clean")
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
