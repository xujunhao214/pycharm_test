import subprocess
import sys
import os
import shutil
import io
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import threading

# 设置标准输出为utf-8编码（解决中文乱码）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

current_script_path = os.path.abspath(__file__)
PROJECT_ROOT = os.path.dirname(current_script_path)


def stream_output(pipe, prefix, is_error=False):
    """实时输出子进程日志（兼容所有编码）"""
    # 尝试多种编码解码字节流
    encodings = ['utf-8', 'gbk', sys.getdefaultencoding(), 'latin-1']
    for line in iter(lambda: pipe.read(1024), b''):  # 按字节读取
        if not line:
            break
        timestamp = datetime.now().strftime('%H:%M:%S')
        # 尝试解码
        decoded_line = "无法解码的内容"
        for encoding in encodings:
            try:
                decoded_line = line.decode(encoding, errors='replace')
                break
            except:
                continue
        # 清理空字符，避免打印异常
        line_clean = decoded_line.rstrip().replace('\0', '')
        # 确保打印时编码兼容
        if is_error:
            print(f'[{timestamp}] {prefix} ERROR: {line_clean}')
        else:
            print(f'[{timestamp}] {prefix}: {line_clean}')
    pipe.close()


def run_test_script(script_path: str, env: str = "test") -> tuple:
    script_name = os.path.basename(script_path)
    prefix = f"[{script_name}]"

    start_time = datetime.now()
    print(f"[{start_time.strftime('%H:%M:%S')}] {prefix} 开始执行 (环境: {env})")

    try:
        # 字节流模式启动子进程（不指定编码）
        process = subprocess.Popen(
            [sys.executable, script_path, env],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {prefix} ERROR: 子进程启动失败: {str(e)}")
        return (script_name, 1, "")

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

    # 结果目录
    if "cloud" in script_name:
        report_dir = os.path.join(PROJECT_ROOT, "report", "cloud_results")
    else:
        report_dir = os.path.join(PROJECT_ROOT, "report", "vps_results")

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"[{end_time.strftime('%H:%M:%S')}] {prefix} 执行完成 (耗时: {duration:.2f}秒)")

    return (script_name, exit_code, report_dir)


def merge_allure_reports(source_dirs: list, merged_dir: str):
    if os.path.exists(merged_dir):
        shutil.rmtree(merged_dir)
    os.makedirs(merged_dir, exist_ok=True)

    for dir in source_dirs:
        if not os.path.exists(dir):
            print(f"警告: 结果目录 {dir} 不存在，跳过合并")
            continue
        for file in os.listdir(dir):
            src = os.path.join(dir, file)
            dst = os.path.join(merged_dir, file)
            if os.path.exists(dst):
                name, ext = os.path.splitext(file)
                dst = os.path.join(merged_dir, f"{name}_{os.path.basename(dir)}{ext}")
            shutil.copy2(src, dst)
    print(f"已合并所有结果到: {merged_dir}")


def run_all_tests_parallel(env: str = "test"):
    test_scripts = [
        "run_vps_tests.py",
        "run_cloud_tests.py"
    ]

    report_root = os.path.join(PROJECT_ROOT, "report")
    os.makedirs(report_root, exist_ok=True)

    for script in test_scripts:
        script_path = os.path.join(PROJECT_ROOT, script)
        if not os.path.exists(script_path):
            print(f"错误: 脚本 {script_path} 不存在")
            return 1

    print(f"\n====== 开始并行执行测试（环境: {env}）======")
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run_test_script, script, env) for script in test_scripts]
        results = [future.result() for future in futures]

    valid_source_dirs = [dir for (_, _, dir) in results if os.path.exists(dir)]
    if not valid_source_dirs:
        print("错误: 无有效测试结果目录，无法合并报告")
        return 1

    merged_results_dir = os.path.join(PROJECT_ROOT, "report", "merged_allure-results")
    merged_report_dir = os.path.join(PROJECT_ROOT, "report", "merged_html-report")

    try:
        print("\n====== 开始合并Allure结果 ======")
        merge_allure_reports(valid_source_dirs, merged_results_dir)

        print("\n====== 开始生成汇总HTML报告 ======")
        os.system(f"allure generate {merged_results_dir} -o {merged_report_dir} --clean")
        report_abs_path = os.path.abspath(merged_report_dir)
        print(f"汇总报告生成成功: file://{report_abs_path}/index.html")
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

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    env = sys.argv[1] if len(sys.argv) > 1 else "test"
    sys.exit(run_all_tests_parallel(env))
