import subprocess
import sys
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import threading


def stream_output(pipe, prefix, is_error=False):
    """实时输出子进程的 stdout 或 stderr"""
    for line in iter(pipe.readline, ''):
        # 添加时间和脚本前缀，区分不同脚本的输出
        timestamp = datetime.now().strftime('%H:%M:%S')
        if is_error:
            # 错误输出标红（控制台支持ANSI的情况下）
            print(f'\033[91m[{timestamp}] {prefix} ERROR: {line.rstrip()}\033[0m')
        else:
            print(f'[{timestamp}] {prefix}: {line.rstrip()}')
    pipe.close()


def run_test_script(script_path: str, env: str = "test") -> tuple:
    """运行单个测试脚本并实时输出"""
    script_name = os.path.basename(script_path)
    prefix = f"[{script_name}]"  # 输出前缀，区分两个脚本

    start_time = datetime.now()
    print(f"\033[94m[{start_time.strftime('%H:%M:%S')}] {prefix} 开始执行 (环境: {env})\033[0m")

    # 启动子进程，不捕获输出（通过管道实时读取）
    process = subprocess.Popen(
        [sys.executable, script_path, env],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )

    # 用线程实时输出 stdout 和 stderr
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

    # 等待进程完成
    exit_code = process.wait()

    # 等待输出线程结束
    stdout_thread.join()
    stderr_thread.join()

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(
        f"\033[94m[{end_time.strftime('%H:%M:%S')}] {prefix} 执行完成 (耗时: {duration:.2f}秒, 退出码: {exit_code})\033[0m")

    return (script_name, exit_code, start_time, end_time)


def run_all_tests_parallel(env: str = "test"):
    """并行执行所有测试脚本（带实时输出）"""
    test_scripts = [
        "run_vps_tests.py",
        "run_cloud_tests.py"
    ]

    # 检查脚本是否存在
    for script in test_scripts:
        if not os.path.exists(script):
            print(f"\033[91m错误: 测试脚本 {script} 不存在，请检查路径\033[0m")
            return

    # 并行执行两个脚本
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run_test_script, script, env) for script in test_scripts]
        results = [future.result() for future in futures]

    # 汇总结果
    print("\n\033[93m========== 测试执行汇总 ==========")
    total_failed = 0
    for script_name, exit_code, start_time, end_time in results:
        status = "失败" if exit_code != 0 else "成功"
        duration = (end_time - start_time).total_seconds()
        if exit_code != 0:
            print(f"{script_name}: \033[91m{status}\033[0m (耗时: {duration:.2f}秒)")
            total_failed += 1
        else:
            print(f"{script_name}: \033[92m{status}\033[0m (耗时: {duration:.2f}秒)")

    if total_failed == 0:
        print("\n\033[92m所有测试脚本执行成功!\033[0m")
        return 0
    else:
        print(f"\n\033[91m有 {total_failed} 个测试脚本执行失败，请查看详细报告\033[0m")
        return 1


if __name__ == "__main__":
    env = sys.argv[1] if len(sys.argv) > 1 else "uat"
    sys.exit(run_all_tests_parallel(env))
