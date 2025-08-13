import pytest
import sys
import os
import subprocess
import multiprocessing
from pathlib import Path
from typing import List, Tuple


def run_test_dir(env: str, report_dir: str, dir_name: str, test_files: List[str]) -> int:
    """单独执行一个目录的测试（串行执行，保证顺序）"""
    print(f"\n===== 开始并行执行 {dir_name} 目录（共{len(test_files)}个文件） =====")

    # 为单个目录构建pytest参数（禁用并行，确保顺序）
    args = [
        "-s",  # 显示标准输出
        "-v",  # 详细输出
        f"--env={env}",  # 指定环境
        f"--alluredir={report_dir}",  # allure结果目录（共享目录，实现结果合并）
        "--order-scope=module",  # 按文件顺序执行
        "--dist=no",  # 禁用并行分发，保证单个目录内串行执行
        *test_files,  # 当前目录的用例文件（按定义顺序）

        # 日志配置（单个进程日志会合并到同一文件）
        "--log-file=./Logs/pytest.log",
        "--log-file-level=info",
        "--log-file-format=%(levelname)-8s %(asctime)s [%(name)s;%(lineno)s]  : %(message)s",
        "--log-file-date-format=%Y-%m-%d %H:%M:%S",
        "--log-level=info"
    ]

    # 执行当前目录的测试并返回退出码
    return pytest.main(args)


def run_tests(env: str = "test") -> int:
    """运行测试并生成报告（两个目录并行，单个目录内串行）"""
    # 配置报告路径
    report_dir = "report/allure-results"
    html_dir = "report/html-report"
    brief_dir = "report/brief-report"

    # 确保报告目录存在
    for dir_path in [report_dir, html_dir, brief_dir]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    # 定义两个目录的用例文件列表（按严格执行顺序排列）
    test_sets: List[Tuple[str, List[str]]] = [
        (
            "test_vps",
            [
                "test_vps/test_create.py",
                # "test_vps/test_vps_Leakage_level.py",
                # "test_vps/test_vps_Leakage_open.py",
                # "test_vps/test_masOrderSend.py",
                # "test_vps/test_vps_ordersend.py",
                "test_vps/test_create_scene.py",
                # "test_vps/test_vps_scene.py",
                # "test_vps/test_vps_money.py",
                "test_vps/test_delete.py",
                "test_vps/test_delete_scene.py",
            ]
        ),
        (
            "test_cloudTrader",
            [
                "test_cloudTrader/test_create.py",
                # "test_cloudTrader/test_cloudOrderSend.py",
                # "test_cloudTrader/test_masOrderSend.py",
                # "test_cloudTrader/test_cloudOrderSend_manageropen.py",
                # "test_cloudTrader/test_cloudOrderSend_managerlevel.py",
                # "test_cloudTrader/test_cloudOrderSend_open.py",
                # "test_cloudTrader/test_cloudOrderSend_level.py",
                "test_cloudTrader/test_create_scene.py",
                # "test_cloudTrader/test_cloudtrader_scene.py",
                # "test_cloudTrader/test_cloudtrader_money.py",
                "test_cloudTrader/test_delete_scene.py",
                "test_cloudTrader/test_delete.py",
            ]
        )
    ]

    # 清理旧的allure结果（避免多进程写入冲突）
    if os.path.exists(report_dir):
        for file in os.listdir(report_dir):
            file_path = os.path.join(report_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"清理旧报告文件失败: {e}")

    # 使用多进程并行执行两个目录的测试
    pool = multiprocessing.Pool(processes=2)  # 固定2个进程，分别对应两个目录
    results = []

    for dir_name, test_files in test_sets:
        # 向进程池提交任务
        result = pool.apply_async(
            run_test_dir,
            args=(env, report_dir, dir_name, test_files)
        )
        results.append(result)

    # 关闭进程池并等待所有任务完成
    pool.close()
    pool.join()

    # 获取两个目录的执行结果（0表示成功，非0表示失败）
    exit_codes = [res.get() for res in results]
    final_exit_code = 0 if all(code == 0 for code in exit_codes) else 1

    # 生成环境文件
    generate_env_cmd = [
        "python", "generate_env.py",
        "--env", env,
        "--output-dir", report_dir
    ]
    result = subprocess.run(
        generate_env_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )
    print(f"测试后生成环境文件输出: {result.stderr}")

    # 生成报告
    try:
        if final_exit_code != 0:
            os.system(f"allure generate {report_dir} -o {html_dir} --clean")
            print(f"测试失败，详细报告: file://{os.path.abspath(html_dir)}/index.html")
        else:
            os.system(f"allure generate {report_dir} -o {brief_dir} --clean --report-type=brief")
            print(f"测试通过，简要报告: file://{os.path.abspath(brief_dir)}/index.html")
    except Exception as e:
        print(f"生成报告失败: {str(e)}")

    return final_exit_code


if __name__ == "__main__":
    # 解决多进程在Windows下的兼容性问题
    multiprocessing.set_start_method('spawn')
    env = sys.argv[1] if len(sys.argv) > 1 else "test"
    sys.exit(run_tests(env))