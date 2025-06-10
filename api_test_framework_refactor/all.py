import pytest
import os
import subprocess
from datetime import datetime

if __name__ == '__main__':
    # 创建报告目录
    report_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"Reports/{report_time}")
    results_dir = os.path.join(report_dir, "results")
    html_report_dir = os.path.join(report_dir, "html_report")

    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(html_report_dir, exist_ok=True)

    # 执行pytest并生成Allure结果
    pytest.main([
        '-v',
        '-s',
        '--alluredir', results_dir,
        '--clean-alluredir',
        'TestCases/test_customer_orders.py'
    ])

    # 生成Allure HTML报告
    try:
        subprocess.run(
            f'allure generate {results_dir} -o {html_report_dir} --clean',
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"Allure报告已生成: {html_report_dir}")

        # 打开报告（可选）
        # subprocess.run(f'allure open {html_report_dir}', shell=True)
    except subprocess.CalledProcessError as e:
        print(f"生成Allure报告失败: {e.stderr.decode()}")
        print("请确保已安装Allure命令行工具: https://docs.qameta.io/allure/#_installing_a_commandline")
