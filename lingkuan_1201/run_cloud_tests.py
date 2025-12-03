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
    # 设置标准输出为utf-8编码
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    current_script_path = os.path.abspath(__file__)
    project_root = os.path.dirname(current_script_path)

    # 核心逻辑：复用run_parallel传递的REPORT_ROOT
    REPORT_ROOT = os.environ.get("REPORT_ROOT", os.path.join(project_root, "report"))
    os.makedirs(REPORT_ROOT, exist_ok=True)

    # 定义目录路径
    report_dir = os.path.join(REPORT_ROOT, "cloud_results")
    html_dir = os.path.join(REPORT_ROOT, "cloud_html")
    markdown_report_path = os.path.join(REPORT_ROOT, "Cloud接口自动化测试报告.md")

    # 创建必要目录
    os.makedirs(report_dir, exist_ok=True)
    os.makedirs(os.path.dirname("./Logs/cloud_pytest.log"), exist_ok=True)

    print(f"当前脚本绝对路径: {os.path.abspath(__file__)}")
    print(f"项目根目录: {project_root}")
    print(f"Cloud 结果目录: {report_dir}")
    print(f"Cloud 报告根目录: {REPORT_ROOT} (Jenkins环境: {'是' if 'JENKINS_URL' in os.environ else '否'})")

    # pytest执行参数
    args = [
        "-s", "-v",
        f"--env={env}",
        f"--test-group=cloud",
        f"--alluredir={report_dir}",
        "--clean-alluredir",
        "test_cloudTrader/test_lianxi.py",
        # 日志配置
        "--log-file=./Logs/cloud_pytest.log",
        "--log-file-level=debug",
        "--log-file-format=%(levelname)-8s - %(asctime)s - [%(module)s:%(lineno)d] - %(message)s",
        "--log-file-date-format=%Y-%m-%d %H:%M:%S",
        "--log-level=debug"
    ]

    try:
        exit_code = pytest.main(args)
        print(f"\nCloud pytest 执行完成，退出码: {exit_code}")
    except Exception as e:
        print(f"\nCloud pytest 执行异常: {str(e)}")
        exit_code = 1

    # 生成环境文件
    markdown_abs_path = os.path.abspath(markdown_report_path)
    standard_path = markdown_abs_path.replace('\\', '/')
    markdown_file_url = f"file:///{standard_path}"
    generate_env_cmd = [
        sys.executable,
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
            encoding="utf-8"
        )
        env_output = result.stdout + result.stderr
        print(f"\nCloud环境文件生成输出: {env_output}")
    except Exception as e:
        print(f"\nCloud 环境文件生成失败: {str(e)}（不影响Markdown报告生成）")

    # 生成Allure独立HTML报告（核心优化：不限定路径+环境区分+容错）
    try:
        # 第一步：判断环境，选择Allure命令
        if os.name == "nt":  # Windows本地
            allure_cmd = "allure"
            cmd = f"chcp 65001 >nul && {allure_cmd} generate {report_dir} -o {html_dir} --clean"
        else:
            if "JENKINS_URL" in os.environ:  # Jenkins环境（Linux）
                # 优先读取Jenkins的Allure环境变量（兼容不同配置）
                allure_cmd = os.environ.get("ALLURE_COMMAND", "allure")
                # Jenkins下若执行失败，直接跳过（汇总报告由Jenkins插件生成）
                cmd = f"{allure_cmd} generate {report_dir} -o {html_dir} --clean || echo 'Jenkins下独立Allure报告生成跳过'"
            else:  # Linux本地
                allure_cmd = "allure"
                cmd = f"{allure_cmd} generate {report_dir} -o {html_dir} --clean"

        # 执行命令
        print(f"\n执行Allure命令: {cmd}")
        os.system(cmd)
        print(f"\nCloud独立HTML报告: file://{os.path.abspath(html_dir)}/index.html")
    except Exception as e:
        # 仅打印错误，不中断流程
        print(f"\nCloud独立HTML报告生成失败: {str(e)}（不影响核心测试流程，汇总Allure报告由Jenkins插件生成）")

    # 生成Markdown报告
    try:
        if os.path.exists(report_dir) and os.listdir(report_dir):
            generate_simple_report(report_dir, env, markdown_report_path)
            print(f"\n✅ Cloud MD报告生成路径: {markdown_report_path}")
        else:
            print(f"\n警告：Allure结果目录 {report_dir} 为空或不存在，未生成Markdown报告")
    except Exception as e:
        print(f"\nMarkdown报告生成失败: {str(e)}")

    return exit_code, report_dir


if __name__ == "__main__":
    env = sys.argv[1] if len(sys.argv) > 1 else "test"
    exit_code, _ = run_cloud_tests(env)
    sys.exit(exit_code)
