import pytest
import sys
import os
import subprocess


def run_vps_tests(env: str = "test"):
    """运行VPS测试，生成独立报告，同时暴露结果目录供合并"""
    # 配置独立报告路径
    report_dir = "/www/python/jenkins/workspace/Documentatio_Test/results"
    html_dir = "/www/python/jenkins/workspace/Documentatio_Test/results/html"

    os.makedirs(report_dir, exist_ok=True)

    # 构建pytest参数
    args = [
        "-s", "-v",
        f"--env={env}",
        f"--test-group=vps",
        f"--alluredir={report_dir}",
        "--clean-alluredir",

        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan_refine_model/test_vps/test_create.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan_refine_model/test_vps/test_masOrderSend.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan_refine_model/test_vps/test_vps_ordersend.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan_refine_model/test_vps/test_vps_orderclose.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan_refine_model/test_vps/test_vpsOrder_open_level.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan_refine_model/test_vps/test_vpsfixed_annotations.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan_refine_model/test_vps/test_create_scene.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan_refine_model/test_vps/test_vpsMasOrder_money_scene.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan_refine_model/test_vps/test_delete.py",

        "--reruns", "3",  # 重试次数
        "--reruns-delay", "10",  # 重试间隔

        "--log-file=./Logs/vps_pytest.log",
        "--log-file-level=info",
        "--log-file-format=%(levelname)-8s %(asctime)s [%(name)s;%(lineno)s]  : %(message)s",
        "--log-file-date-format=%Y-%m-%d %H:%M:%S",
        "--log-level=info"
    ]

    # 执行测试
    exit_code = pytest.main(args)

    # 生成环境文件
    generate_env_cmd = [
        "python", "generate_env.py",
        "--env", env, "--output-dir", report_dir
    ]
    result = subprocess.run(
        generate_env_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )
    print(f"VPS测试环境文件生成输出: {result.stderr}")

    # 生成独立HTML报告
    try:
        if exit_code != 0:
            os.system(f"allure generate {report_dir} -o {html_dir} --clean")
            print(f"VPS独立报告: file://{os.path.abspath(html_dir)}/index.html")
    except Exception as e:
        print(f"VPS独立报告生成失败: {str(e)}")

    # 返回结果目录（供并行脚本合并）
    return exit_code, report_dir


if __name__ == "__main__":
    env = sys.argv[1] if len(sys.argv) > 1 else "test"
    exit_code, _ = run_vps_tests(env)
    sys.exit(exit_code)
