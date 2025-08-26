import subprocess
import sys
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import threading


def stream_output(pipe, prefix, is_error=False):
    """实时输出子进程日志"""
    for line in iter(pipe.readline, ''):
        timestamp = datetime.now().strftime('%H:%M:%S')
        if is_error:
            print(f'\033[91m[{timestamp}] {prefix} ERROR: {line.rstrip()}\033[0m')
        else:
            print(f'[{timestamp}] {prefix}: {line.rstrip()}')
    pipe.close()


def run_test_script(script_path: str, env: str = "test") -> tuple:
    """运行单个测试脚本，返回退出码和结果目录"""
    script_name = os.path.basename(script_path)
    prefix = f"[{script_name}]"

    start_time = datetime.now()
    print(f"\033[94m[{start_time.strftime('%H:%M:%S')}] {prefix} 开始执行 (环境: {env})\033[0m")

    # 启动子进程并捕获返回值（包含结果目录）
    process = subprocess.Popen(
        [sys.executable, script_path, env],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )

    # 实时输出线程
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

    # 解析子脚本返回的结果目录（通过stdout捕获，需子脚本配合打印）
    # 注：此处通过约定路径获取，更稳定（子脚本结果目录固定）
    if "cloud" in script_name:
        report_dir = "report/cloud_allure-results"
    else:
        report_dir = "report/vps_allure-results"

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"\033[94m[{end_time.strftime('%H:%M:%S')}] {prefix} 执行完成 (耗时: {duration:.2f}秒)\033[0m")

    return (script_name, exit_code, report_dir)


def merge_allure_reports(source_dirs: list, merged_dir: str):
    """合并多个Allure结果目录"""
    # 清理合并目录
    if os.path.exists(merged_dir):
        shutil.rmtree(merged_dir)
    os.makedirs(merged_dir, exist_ok=True)

    # 复制所有结果文件到合并目录
    for dir in source_dirs:
        if not os.path.exists(dir):
            print(f"\033[93m警告: 结果目录 {dir} 不存在，跳过合并\033[0m")
            continue
        for file in os.listdir(dir):
            src = os.path.join(dir, file)
            dst = os.path.join(merged_dir, file)
            # 处理同名文件（添加前缀避免冲突）
            if os.path.exists(dst):
                name, ext = os.path.splitext(file)
                dst = os.path.join(merged_dir, f"{name}_{os.path.basename(dir)}{ext}")
            shutil.copy2(src, dst)
    print(f"已合并结果到: {merged_dir}")


def run_all_tests_parallel(env: str = "test"):
    """并行执行测试并生成合并报告"""
    test_scripts = [
        "run_vps_tests.py",
        "run_cloud_tests.py"
    ]

    # 检查脚本存在性
    for script in test_scripts:
        if not os.path.exists(script):
            print(f"\033[91m错误: 脚本 {script} 不存在\033[0m")
            return 1

    # 并行执行，获取每个脚本的结果目录
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run_test_script, script, env) for script in test_scripts]
        results = [future.result() for future in futures]

    # 提取结果目录
    source_dirs = [report_dir for (_, _, report_dir) in results]
    merged_results_dir = "report/merged_allure-results"  # 合并结果目录
    merged_report_dir = "report/merged_html-report"  # 合并HTML报告

    # 合并结果并生成汇总报告
    try:
        # 合并Allure结果
        merge_allure_reports(source_dirs, merged_results_dir)

        # 生成汇总HTML报告
        print("\n开始生成汇总报告...")
        os.system(f"allure generate {merged_results_dir} -o {merged_report_dir} --clean")
        print(f"\033[92m汇总报告生成成功: file://{os.path.abspath(merged_report_dir)}/index.html\033[0m")
    except Exception as e:
        print(f"\033[91m汇总报告生成失败: {str(e)}\033[0m")

    # 输出执行汇总
    print("\n\033[93m========== 测试汇总 ==========")
    total_failed = 0
    for script_name, exit_code, _ in results:
        status = "失败" if exit_code != 0 else "成功"
        if exit_code != 0:
            print(f"{script_name}: \033[91m{status}\033[0m")
            total_failed += 1
        else:
            print(f"{script_name}: \033[92m{status}\033[0m")

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    env = sys.argv[1] if len(sys.argv) > 1 else "test"
    sys.exit(run_all_tests_parallel(env))
