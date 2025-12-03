import subprocess
import sys
import os
import shutil
import io
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import threading
from report_generator import generate_simple_report
from generate_env import generate_merged_env, get_pure_report_paths  # 新增导入

current_script_path = os.path.abspath(__file__)
PROJECT_ROOT = os.path.dirname(current_script_path)


def stream_output(pipe, prefix, is_error=False):
    encodings = ['utf-8', 'gbk', sys.getdefaultencoding(), 'latin-1']
    for line in iter(lambda: pipe.read(1024), b''):
        if not line:
            break
        timestamp = datetime.now().strftime('%H:%M:%S')
        decoded_line = "无法解码的内容"
        for encoding in encodings:
            try:
                decoded_line = line.decode(encoding, errors='replace')
                break
            except:
                continue
        line_clean = decoded_line.rstrip().replace('\0', '')
        if is_error:
            print(f'[{timestamp}] {prefix} ERROR: {line_clean}')
        else:
            print(f'[{timestamp}] {prefix}: {line_clean}')
    pipe.close()


def run_test_script(script_path: str, env: str = "test", report_root: str = "") -> tuple:
    script_name = os.path.basename(script_path)
    prefix = f"[{script_name}]"

    start_time = datetime.now()
    print(f"[{start_time.strftime('%H:%M:%S')}] {prefix} 开始执行 (环境: {env})")

    try:
        env_vars = os.environ.copy()
        env_vars["REPORT_ROOT"] = report_root
        process = subprocess.Popen(
            [sys.executable, script_path, env],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env_vars
        )
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {prefix} ERROR: 子进程启动失败: {str(e)}")
        return (script_name, 1, "")

    stdout_thread = threading.Thread(
        target=stream_output,
        args=(process.stdout, prefix, False),
        daemon=True
    )
    stderr_thread = threading.Thread(
        target=stream_output,
        args=(process.stderr, prefix, True),
        daemon=True
    )

    stdout_thread.start()
    stderr_thread.start()
    exit_code = process.wait()
    stdout_thread.join()
    stderr_thread.join()

    if "cloud" in script_name:
        report_dir = os.path.join(report_root, "cloud_results")
    else:
        report_dir = os.path.join(report_root, "vps_results")

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"[{end_time.strftime('%H:%M:%S')}] {prefix} 执行完成 (耗时: {duration:.2f}秒)")

    return (script_name, exit_code, report_dir)


def merge_allure_reports(source_dirs: list, merged_dir: str):
    if os.path.exists(merged_dir):
        shutil.rmtree(merged_dir)
    os.makedirs(merged_dir, exist_ok=True)

    for dir in source_dirs:
        if not os.path.exists(dir) or not os.listdir(dir):
            print(f"警告: 结果目录 {dir} 不存在或为空，跳过合并")
            continue
        for file in os.listdir(dir):
            src = os.path.join(dir, file)
            dst = os.path.join(merged_dir, file)
            if os.path.exists(dst):
                dir_prefix = os.path.basename(dir).replace("_results", "")
                name, ext = os.path.splitext(file)
                dst = os.path.join(merged_dir, f"{dir_prefix}_{name}{ext}")
            shutil.copy2(src, dst)
    print(f"已合并所有结果到: {merged_dir}")


def run_all_tests_parallel(env: str = "test"):
    test_scripts = [
        "run_vps_tests.py",
        "run_cloud_tests.py"
    ]

    # 核心逻辑：仅Jenkins环境生成带构建号的目录，本地用固定目录
    if "JENKINS_URL" in os.environ:
        build_number = os.environ.get("BUILD_NUMBER", datetime.now().strftime("%Y%m%d%H%M%S"))
        # 报告根目录直接指向workspace下的report
        report_root = os.path.join(PROJECT_ROOT, "report", f"build_{build_number}")
    else:
        report_root = os.path.join(PROJECT_ROOT, "report")
    os.makedirs(report_root, exist_ok=True)
    print(f"当前构建报告根目录: {report_root} (Jenkins环境: {'是' if 'JENKINS_URL' in os.environ else '否'})")

    for script in test_scripts:
        script_path = os.path.join(PROJECT_ROOT, script)
        if not os.path.exists(script_path):
            print(f"错误: 脚本 {script_path} 不存在")
            return 1

    print(f"\n====== 开始并行执行测试（环境: {env}）======")
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run_test_script, script, env, report_root) for script in test_scripts]
        results = [future.result() for future in futures]

    valid_source_dirs = [dir for (_, _, dir) in results if os.path.exists(dir) and os.listdir(dir)]
    if not valid_source_dirs:
        print("错误: 无有效测试结果目录，无法合并报告")
        return 1

    # 所有汇总报告路径基于report_root（Jenkins带构建号，本地固定）
    merged_results_dir = os.path.join(report_root, "merged_allure-results")
    merged_html_dir = os.path.join(report_root, "merged_html-report")
    merged_markdown_path = os.path.join(report_root, "汇总接口自动化测试报告.md")

    try:
        print("\n====== 开始合并Allure结果 ======")
        merge_allure_reports(valid_source_dirs, merged_results_dir)

        print("\n====== 开始生成汇总Markdown报告 ======")
        generate_simple_report(merged_results_dir, env, merged_markdown_path)
        merged_markdown_abs = os.path.abspath(merged_markdown_path)
        # 关键修正：调用工具函数生成正确链接（替换手动拼接）
        markdown_file_url, _ = get_pure_report_paths(merged_markdown_abs)
        print(f"汇总Markdown报告（带协议路径）: {markdown_file_url}")

        print("\n====== 生成合并环境文件（供HTML报告使用）======")
        generate_merged_env(merged_results_dir, markdown_file_url, env_value=env)

        print("\n====== 开始生成汇总HTML报告（读取最新环境文件）======")
        if os.path.exists(merged_html_dir):
            shutil.rmtree(merged_html_dir)
        # 关键修正：Jenkins用Allure绝对路径，本地用allure
        if "JENKINS_URL" in os.environ:
            allure_cmd = "/var/lib/jenkins/tools/ru.yandex.qatools.allure.jenkins.tools.AllureCommandlineInstallation/Allure2.12.0/bin/allure"
            os.system(f"{allure_cmd} generate {merged_results_dir} -o {merged_html_dir} --clean")
        else:
            os.system(f"chcp 65001 >nul && allure generate {merged_results_dir} -o {merged_html_dir} --clean")
        merged_html_abs = os.path.abspath(merged_html_dir)
        print(f"汇总HTML报告生成成功: file://{merged_html_abs}/index.html")

    except Exception as e:
        print(f"错误: 汇总报告生成失败: {str(e)}")
        return 1

    print("\n====== 测试执行汇总 ======")
    total_failed = 0
    for script_name, exit_code, _ in results:
        status = "成功" if exit_code == 0 else "失败"
        print(f"{script_name}: {status}（退出码: {exit_code}）")
        if exit_code != 0:
            total_failed += 1

    print("\n====== 所有报告路径 ======")
    print(f"1. VPS独立Markdown报告: {os.path.join(report_root, 'VPS接口自动化测试报告.md')}")
    print(f"2. Cloud独立Markdown报告: {os.path.join(report_root, 'Cloud接口自动化测试报告.md')}")
    print(f"3. 汇总HTML报告: file://{merged_html_abs}/index.html")
    print(f"4. 汇总Markdown报告: {merged_markdown_abs}")

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    env = sys.argv[1] if len(sys.argv) > 1 else "uat"
    sys.exit(run_all_tests_parallel(env))
