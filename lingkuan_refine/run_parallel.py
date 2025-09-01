import subprocess
import sys
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import threading


def stream_output(pipe, prefix, is_error=False):
    """
    实时输出子进程日志（优化编码解码：优先GBK，兼容UTF-8，避免UnicodeDecodeError）
    :param pipe: 子进程输出管道（stdout/stderr）
    :param prefix: 日志前缀（脚本名）
    :param is_error: 是否为错误输出
    """
    for line_bytes in iter(pipe.readline, b''):
        timestamp = datetime.now().strftime('%H:%M:%S')
        try:
            # 优先尝试GB2312解码（适配Windows控制台默认输出）
            line = line_bytes.decode('gb2312').rstrip()
        except UnicodeDecodeError:
            try:
                line = line_bytes.decode('gbk').rstrip()
            except UnicodeDecodeError:
                line = line_bytes.decode('utf-8', errors='replace').rstrip()

        # 按错误/正常输出区分格式
        if is_error:
            print(f'[{timestamp}] {prefix} ERROR: {line}')
        else:
            print(f'[{timestamp}] {prefix}: {line}')

    pipe.close()


def run_test_script(script_path: str, env: str = "test") -> tuple:
    """运行单个测试脚本，返回（脚本名、退出码、结果目录）"""
    script_name = os.path.basename(script_path)
    prefix = f"[{script_name}]"

    start_time = datetime.now()
    print(f"[{start_time.strftime('%H:%M:%S')}] {prefix} 开始执行 (环境: {env})")

    # 关键修改：不指定text=True和encoding（默认返回字节流），避免自动UTF-8解码
    process = subprocess.Popen(
        [sys.executable, script_path, env],
        stdout=subprocess.PIPE,  # 输出字节流
        stderr=subprocess.PIPE,  # 错误字节流
    )

    # 启动实时输出线程（处理字节流）
    stdout_thread = threading.Thread(
        target=stream_output,
        args=(process.stdout, prefix, False),
        daemon=True  # 主线程退出时自动关闭子线程
    )
    stderr_thread = threading.Thread(
        target=stream_output,
        args=(process.stderr, prefix, True),
        daemon=True
    )

    stdout_thread.start()
    stderr_thread.start()

    # 等待子进程结束，获取退出码
    try:
        exit_code = process.wait()  # 等待脚本执行完成
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {prefix} 执行异常: {str(e)}")
        exit_code = 1  # 异常时标记为失败

    # 等待输出线程处理完剩余内容
    stdout_thread.join(timeout=5)  # 5秒超时，避免线程卡死
    stderr_thread.join(timeout=5)

    # 约定结果目录（按脚本类型区分，保持原逻辑）
    if "cloud" in script_name:
        report_dir = "report/cloud_allure-results"
    else:
        report_dir = "report/vps_allure-results"

    # 计算执行耗时
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"[{end_time.strftime('%H:%M:%S')}] {prefix} 执行完成 (耗时: {duration:.2f}秒)")

    return (script_name, exit_code, report_dir)


def merge_allure_reports(source_dirs: list, merged_dir: str):
    """合并多个Allure结果目录（补充异常处理，避免合并失败）"""
    # 清理合并目录（添加异常捕获）
    if os.path.exists(merged_dir):
        try:
            shutil.rmtree(merged_dir)
        except PermissionError:
            print(f"警告: 无法删除旧合并目录 {merged_dir}（文件被占用），将覆盖内容")
        except Exception as e:
            print(f"警告: 清理旧合并目录失败: {str(e)}，将覆盖内容")

    # 确保合并目录存在
    os.makedirs(merged_dir, exist_ok=True)

    # 复制结果文件（处理同名文件冲突）
    for dir in source_dirs:
        if not os.path.exists(dir):
            print(f"警告: 结果目录 {dir} 不存在，跳过合并")
            continue

        # 遍历目录下的文件（仅处理Allure结果文件，避免无关文件）
        for file in os.listdir(dir):
            file_path = os.path.join(dir, file)
            # 只合并Allure识别的结果文件（json/xml格式）
            if not (file.endswith(".json") or file.endswith(".xml") or file.endswith(".txt")):
                continue

            # 目标路径（处理同名文件：添加原目录前缀）
            dst_path = os.path.join(merged_dir, file)
            if os.path.exists(dst_path):
                name, ext = os.path.splitext(file)
                # 用原目录名作为后缀，避免同名覆盖
                dst_path = os.path.join(merged_dir, f"{name}_{os.path.basename(dir)}{ext}")

            # 复制文件（添加异常捕获）
            try:
                shutil.copy2(file_path, dst_path)
            except Exception as e:
                print(f"警告: 复制文件 {file_path} 失败: {str(e)}，跳过该文件")

    print(f"已合并结果到: {merged_dir}")


def run_all_tests_parallel(env: str = "test"):
    """并行执行测试并生成合并报告（补充参数校验和异常捕获）"""
    test_scripts = [
        "run_vps_tests.py",
        "run_cloud_tests.py"
    ]

    # 1. 校验脚本存在性（提前报错，避免白跑）
    missing_scripts = [s for s in test_scripts if not os.path.exists(s)]
    if missing_scripts:
        print(f"错误: 以下脚本不存在，无法执行测试: {', '.join(missing_scripts)}")
        return 1

    # 2. 校验Allure是否安装（避免生成报告时失败）
    if shutil.which("allure") is None:
        print("错误: 未找到Allure命令行工具，请先安装Allure并配置到环境变量")
        return 1

    # 3. 并行执行测试脚本
    print(f"\n=== 开始并行执行测试（环境: {env}）===")
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            # 提交任务到线程池
            futures = [executor.submit(run_test_script, script, env) for script in test_scripts]
            # 获取所有任务结果（阻塞直到全部完成）
            results = [future.result(timeout=3600) for future in futures]  # 1小时超时
    except TimeoutError:
        print("错误: 测试执行超时（超过1小时），强制终止")
        return 1
    except Exception as e:
        print(f"错误: 并行执行测试时发生异常: {str(e)}")
        return 1

    # 4. 提取结果目录，准备合并
    source_dirs = [report_dir for (_, _, report_dir) in results]
    merged_results_dir = "report/merged_allure-results"
    merged_report_dir = "report/merged_html-report"

    # 5. 合并Allure结果并生成HTML报告
    print("\n=== 开始处理测试结果 ===")
    try:
        merge_allure_reports(source_dirs, merged_results_dir)

        # 生成HTML报告（--clean确保覆盖旧报告）
        print("\n开始生成汇总HTML报告...")
        allure_cmd = f"allure generate {merged_results_dir} -o {merged_report_dir} --clean"
        # 执行Allure命令并捕获输出（避免命令执行失败无提示）
        allure_process = subprocess.run(
            allure_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8"
        )
        if allure_process.returncode != 0:
            print(f"警告: 生成HTML报告时Allure命令执行失败: {allure_process.stderr}")
        else:
            # 生成可直接访问的本地路径（适配Windows）
            report_abspath = os.path.abspath(merged_report_dir)
            report_url = f"file:///{report_abspath.replace(os.sep, '/')}/index.html"
            print(f"汇总报告生成成功: {report_url}")
    except Exception as e:
        print(f"错误: 处理测试结果失败: {str(e)}")
        return 1

    # 6. 输出测试汇总
    print("\n========== 测试汇总 ==========")
    total_failed = 0
    for script_name, exit_code, _ in results:
        status = "成功" if exit_code == 0 else "失败"
        print(f"{script_name}: {status}")
        if exit_code != 0:
            total_failed += 1

    # 返回整体状态（0=全部成功，1=至少一个失败）
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    # 处理命令行参数（支持指定环境，默认uat）
    env = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in ["test", "uat"] else "uat"
    # 执行主逻辑并返回退出码
    sys.exit(run_all_tests_parallel(env))
