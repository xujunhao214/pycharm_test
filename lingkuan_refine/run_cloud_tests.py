import pytest
import sys
import os
import subprocess


def run_cloud_tests(env: str = "test"):
    """运行CloudTrader测试，生成独立报告，同时暴露结果目录供合并"""
    # 配置独立报告路径（保持原有稳定逻辑）
    report_dir = "/www/python/jenkins/workspace/Documentatio_Test/results"
    html_dir = "/www/python/jenkins/workspace/Documentatio_Test/results/html"

    # 确保目录存在
    os.makedirs(report_dir, exist_ok=True)

    # 构建pytest参数（保留原有稳定配置）
    args = [
        "-s", "-v",
        f"--env={env}",
        f"--test-group=cloud",
        f"--alluredir={report_dir}",
        "--clean-alluredir",

        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan_refine/test_cloudTrader/test_create.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan_refine/test_cloudTrader/test_getAccountDataPage.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan_refine/test_cloudTrader/test_cloudOrderSend.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan_refine/test_cloudTrader/test_cloudOrderClose.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan_refine/test_cloudTrader/test_cloud_masOrderSend.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan_refine/test_cloudTrader/test_cloud_masOrderClose.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan_refine/test_cloudTrader/test_cloudOrder_open_level.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan_refine/test_cloudTrader/test_cloudfixed_annotations.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan_refine/test_cloudTrader/test_create_scene.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan_refine/test_cloudTrader/test_cloudtrader_money_scene.py",
        "/www/python/jenkins/workspace/Documentatio_Test/lingkuan_refine/test_cloudTrader/test_delete.py",
        # "/www/python/jenkins/workspace/Documentatio_Test/lingkuan_refine/test_cloudTrader/test_lianxi.py",

        "--log-file=./Logs/cloud_pytest.log",
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
    print(f"Cloud文件生成输出: {result.stderr}")

    # 生成独立HTML报告（沿用原有稳定逻辑）
    try:
        if exit_code != 0:
            os.system(f"allure generate {report_dir} -o {html_dir} --clean")
            print(f"Cloud独立报告: file://{os.path.abspath(html_dir)}/index.html")
    except Exception as e:
        print(f"Cloud独立报告生成失败: {str(e)}")

    # 返回结果目录（供并行脚本合并）
    return exit_code, report_dir


if __name__ == "__main__":
    env = sys.argv[1] if len(sys.argv) > 1 else "uat"
    exit_code, _ = run_cloud_tests(env)
    sys.exit(exit_code)
