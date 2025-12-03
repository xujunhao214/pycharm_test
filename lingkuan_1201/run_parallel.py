import subprocess
import sys
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import threading
from report_generator import generate_simple_report
from generate_env import generate_merged_env

current_script_path = os.path.abspath(__file__)
PROJECT_ROOT = os.path.dirname(current_script_path)


def stream_output(pipe, prefix, is_error=False):
    encodings = ['utf-8', 'gbk', sys.getdefaultencoding()]
    for line in iter(lambda: pipe.read(1024), b''):
        if not line:
            break
        timestamp = datetime.now().strftime('%H:%M:%S')
        decoded_line = "无法解码"
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


def run_test_script(script_path: str, env: str, report_root: str) -> tuple:
    script_name = os.path.basename(script_path)
    prefix = f"[{script_name}]"
    start_time = datetime.now()
    print(f"[{start_time.strftime('%H:%M:%S')}] {prefix} 开始执行 (环境: {env})")

    try:
        # 传递REPORT_ROOT给子脚本（VPS/Cloud脚本需读取此变量）
        env_vars = os.environ.copy()
        env_vars["REPORT_ROOT"] = report_root
        process = subprocess.Popen(
            [sys.executable, script_path, env],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env_vars
        )
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {prefix} 启动失败: {str(e)}")
        return (script_name, 1, "")

    stdout_thread = threading.Thread(target=stream_output, args=(process.stdout, prefix, False), daemon=True)
    stderr_thread = threading.Thread(target=stream_output, args=(process.stderr, prefix, True), daemon=True)
    stdout_thread.start()
    stderr_thread.start()
    exit_code = process.wait()
    stdout_thread.join()
    stderr_thread.join()

    # 子脚本的结果目录（基于report_root）
    report_dir = os.path.join(report_root, f"{script_name.split('_')[1]}_results")  # 如vps_results
    end_time = datetime.now()
    print(
        f"[{end_time.strftime('%H:%M:%S')}] {prefix} 执行完成 (耗时: {(end_time - start_time).total_seconds():.2f}秒)")
    return (script_name, exit_code, report_dir)


def merge_allure_reports(source_dirs: list, merged_dir: str):
    if os.path.exists(merged_dir):
        shutil.rmtree(merged_dir)
    os.makedirs(merged_dir, exist_ok=True)
    for dir in source_dirs:
        if not os.path.exists(dir) or not os.listdir(dir):
            print(f"警告: 结果目录 {dir} 为空，跳过")
            continue
        for file in os.listdir(dir):
            src = os.path.join(dir, file)
            dst = os.path.join(merged_dir, f"{os.path.basename(dir).replace('_results', '')}_{file}")
            shutil.copy2(src, dst)
    print(f"合并结果到: {merged_dir}")


def run_all_tests_parallel(env: str = "test"):
    test_scripts = ["run_vps_tests.py", "run_cloud_tests.py"]

    # 核心：区分Jenkins/本地环境的报告根目录
    if "JENKINS_URL" in os.environ:
        # Jenkins：报告根目录=report/build_${BUILD_NUMBER}（保留历史）
        build_number = os.environ.get("BUILD_NUMBER", datetime.now().strftime("%Y%m%d%H%M%S"))
        report_root = os.path.join(PROJECT_ROOT, "report", f"build_{build_number}")
    else:
        # 本地：报告根目录=report（固定目录）
        report_root = os.path.join(PROJECT_ROOT, "report")
    os.makedirs(report_root, exist_ok=True)
    print(f"报告根目录: {report_root} (Jenkins环境: {'是' if 'JENKINS_URL' in os.environ else '否'})")

    # 检查脚本是否存在
    for script in test_scripts:
        script_path = os.path.join(PROJECT_ROOT, script)
        if not os.path.exists(script_path):
            print(f"错误: 脚本 {script_path} 不存在")
            return 1

    # 并行执行测试
    print(f"\n====== 并行执行测试（环境: {env}）======")
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run_test_script, os.path.join(PROJECT_ROOT, s), env, report_root) for s in
                   test_scripts]
        results = [f.result() for f in futures]

    # 收集有效结果目录
    valid_source_dirs = [d for (_, _, d) in results if os.path.exists(d) and os.listdir(d)]
    if not valid_source_dirs:
        print("错误: 无有效结果目录")
        return 1

    # 汇总报告路径（基于report_root）
    merged_results_dir = os.path.join(report_root, "merged_allure-results")
    merged_html_dir = os.path.join(report_root, "merged_html-report")
    merged_markdown_path = os.path.join(report_root, "汇总接口自动化测试报告.md")

    try:
        print("\n====== 合并Allure结果 ======")
        merge_allure_reports(valid_source_dirs, merged_results_dir)

        print("\n====== 生成汇总MD报告 ======")
        generate_simple_report(merged_results_dir, env, merged_markdown_path)
        merged_markdown_abs = os.path.abspath(merged_markdown_path)
        print(f"汇总MD报告: {merged_markdown_abs}")

        print("\n====== 生成合并环境文件 ======")
        generate_merged_env(merged_results_dir, merged_markdown_abs, env)

        print("\n====== 生成汇总HTML报告 ======")
        if os.path.exists(merged_html_dir):
            shutil.rmtree(merged_html_dir)
        # 适配Windows/Linux的Allure命令
        if os.name == "nt":
            os.system(f"chcp 65001 >nul && allure generate {merged_results_dir} -o {merged_html_dir} --clean")
        else:
            os.system(f"allure generate {merged_results_dir} -o {merged_html_dir} --clean")
        print(f"汇总HTML报告: {os.path.abspath(merged_html_dir)}/index.html")

    except Exception as e:
        print(f"错误: 汇总报告生成失败: {str(e)}")
        return 1

    # 执行汇总
    print("\n====== 测试汇总 ======")
    total_failed = sum(1 for (_, code, _) in results if code != 0)
    for script_name, code, _ in results:
        print(f"{script_name}: {'成功' if code == 0 else '失败'}（退出码: {code}）")

    print("\n====== 所有报告路径 ======")
    print(f"1. VPS结果目录: {os.path.join(report_root, 'vps_results')}")
    print(f"2. Cloud结果目录: {os.path.join(report_root, 'cloud_results')}")
    print(f"3. 汇总MD报告: {merged_markdown_abs}")
    print(f"4. 汇总HTML报告: {os.path.abspath(merged_html_dir)}/index.html")

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    env = sys.argv[1] if len(sys.argv) > 1 else "test"
    sys.exit(run_all_tests_parallel(env))
