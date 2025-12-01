# -*- coding: utf-8 -*-
import pytest
import sys
import os
import subprocess
import io
from datetime import datetime
from report_generator import generate_simple_report
import xml.etree.ElementTree as ET


def run_cloud_tests(env: str = "test"):
    # 设置标准输出为utf-8编码（解决print中文乱码）
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    current_script_path = os.path.abspath(__file__)
    project_root = os.path.dirname(current_script_path)

    # ========== 核心修改1：读取Jenkins构建号，生成带序号的报告根目录 ==========
    # Jenkins环境用BUILD_NUMBER，本地用时间戳（兼容本地调试）
    build_number = os.environ.get("BUILD_NUMBER", datetime.now().strftime("%Y%m%d%H%M%S"))
    report_root = os.path.join(project_root, "report", f"build_{build_number}")
    os.makedirs(report_root, exist_ok=True)

    # ========== 核心修改2：所有路径基于带序号的report_root生成 ==========
    report_dir = os.path.join(report_root, "cloud_results")  # allure结果目录
    html_dir = os.path.join(report_root, "cloud_html")  # allure HTML报告目录
    markdown_report_path = os.path.join(report_root, "Cloud接口自动化测试报告.md")  # Cloud专属Markdown报告
    log_dir = os.path.join(project_root, "Logs")  # 日志目录（保持项目根目录，避免分散）

    # 创建必要目录（确保目录存在，避免报错）
    os.makedirs(report_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    print(f"当前脚本绝对路径: {os.path.abspath(__file__)}")
    print(f"项目根目录: {project_root}")
    print(f"Cloud 结果目录: {report_dir}")
    print(f"带序号的报告根目录: {report_root}")  # 新增日志，便于调试

    # pytest执行参数（核心保留--alluredir，确保生成Allure结果）
    args = [
        "-s", "-v",
        f"--env={env}",
        f"--test-group=cloud",
        f"--alluredir={report_dir}",
        "--clean-alluredir",  # 清理旧结果，避免数据残留

        # 测试用例（按需调整）
        "test_cloudTrader/test_lianxi.py",

        # 日志配置（修改为绝对路径，避免Jenkins路径错乱）
        f"--log-file={os.path.join(log_dir, 'cloud_pytest.log')}",
        "--log-file-level=debug",
        "--log-file-format=%(levelname)-8s - %(asctime)s - [%(module)s:%(lineno)d] - %(message)s",
        "--log-file-date-format=%Y-%m-%d %H:%M:%S",
        "--log-level=debug"
    ]

    try:
        # 执行pytest生成Allure结果
        exit_code = pytest.main(args)
        print(f"\nCloud pytest 执行完成，退出码: {exit_code}")
    except Exception as e:
        print(f"\nCloud pytest 执行异常: {str(e)}")
        exit_code = 1

    # 生成环境文件（调用generate_env.py，传递带序号的路径）
    markdown_abs_path = os.path.abspath(markdown_report_path)
    standard_path = markdown_abs_path.replace('\\', '/')
    markdown_file_url = f"file:///{standard_path}"
    generate_env_cmd = [
        sys.executable,  # 替换python为sys.executable，兼容多Python环境
        os.path.join(project_root, "generate_env.py"),  # 绝对路径调用，避免找不到脚本
        "--env", env,
        "--output-dir", report_dir,
        "--markdown-report-path", markdown_file_url
    ]
    try:
        result = subprocess.run(
            generate_env_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8"  # 直接指定编码，避免手动解码
        )
        # 打印环境文件生成日志
        if result.stdout:
            print(f"\nCloud环境文件生成日志: {result.stdout}")
        if result.stderr:
            print(f"\nCloud环境文件生成错误: {result.stderr}")
    except Exception as e:
        print(f"\nCloud 环境文件生成失败: {str(e)}（不影响Markdown报告生成）")

    # 生成Cloud独立Allure HTML报告（兼容Linux/Windows，移除chcp）
    try:
        if os.name == "nt":  # Windows系统
            os.system(f"chcp 65001 >nul && allure generate {report_dir} -o {html_dir} --clean")
        else:  # Linux/Mac/Jenkins
            os.system(f"allure generate {report_dir} -o {html_dir} --clean")
        print(f"\nCloud独立HTML报告: file://{os.path.abspath(html_dir)}/index.html")
    except Exception as e:
        print(f"\nCloud独立HTML报告生成失败: {str(e)}（不影响Markdown报告生成）")

    # 核心：调用简化后的Markdown报告生成函数（仅传3个必要参数）
    try:
        if os.path.exists(report_dir) and os.listdir(report_dir):
            generate_simple_report(report_dir, env, markdown_report_path)
            print(f"\n✅ Cloud MD报告生成成功：{markdown_report_path}")
        else:
            print(f"\n警告：Allure结果目录 {report_dir} 为空或不存在，未生成Markdown报告")
    except Exception as e:
        print(f"\nMarkdown报告生成失败: {str(e)}")

    return exit_code, report_dir


if __name__ == "__main__":
    env = sys.argv[1] if len(sys.argv) > 1 else "test"
    exit_code, _ = run_cloud_tests(env)
    sys.exit(exit_code)