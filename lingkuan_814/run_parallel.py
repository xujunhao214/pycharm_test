import subprocess
import sys
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime


def run_test_script(script_path: str, env: str = "test") -> tuple:
    """
    运行单个测试脚本
    :param script_path: 脚本路径
    :param env: 测试环境
    :return: (脚本名称, 退出码, 开始时间, 结束时间)
    """
    script_name = os.path.basename(script_path)
    start_time = datetime.now()
    print(f"[{start_time.strftime('%H:%M:%S')}] 开始执行 {script_name} (环境: {env})")

    # 执行测试脚本
    result = subprocess.run(
        [sys.executable, script_path, env],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(
        f"[{end_time.strftime('%H:%M:%S')}] {script_name} 执行完成 (耗时: {duration:.2f}秒, 退出码: {result.returncode})")

    # 输出脚本的错误信息（如果有的话）
    if result.stderr:
        print(f"\n{script_name} 错误输出:\n{result.stderr}\n")

    return (script_name, result.returncode, start_time, end_time)


def run_all_tests_parallel(env: str = "test"):
    """并行执行所有测试脚本"""
    # 测试脚本路径列表
    test_scripts = [
        "run_vps_tests.py",
        "run_cloud_tests.py"
    ]

    # 检查脚本是否存在
    for script in test_scripts:
        if not os.path.exists(script):
            print(f"错误: 测试脚本 {script} 不存在，请检查路径")
            return

    # 使用线程池并行执行
    with ThreadPoolExecutor(max_workers=2) as executor:
        # 提交任务
        futures = [executor.submit(run_test_script, script, env) for script in test_scripts]

        # 等待所有任务完成并收集结果
        results = [future.result() for future in futures]

    # 汇总结果
    print("\n===== 测试执行汇总 =====")
    total_failed = 0
    for script_name, exit_code, start_time, end_time in results:
        status = "失败" if exit_code != 0 else "成功"
        duration = (end_time - start_time).total_seconds()
        print(f"{script_name}: {status} (耗时: {duration:.2f}秒)")
        if exit_code != 0:
            total_failed += 1

    # 输出最终结论
    if total_failed == 0:
        print("\n所有测试脚本执行成功!")
        return 0
    else:
        print(f"\n有 {total_failed} 个测试脚本执行失败，请查看详细报告")
        return 1


if __name__ == "__main__":
    # 从命令行获取环境参数，默认test环境
    env = sys.argv[1] if len(sys.argv) > 1 else "test"
    sys.exit(run_all_tests_parallel(env))
