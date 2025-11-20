import json
import os
from datetime import datetime
from collections import defaultdict  # 导入分组所需模块
from lingkuan_1114.config import ENV_CONFIG, Environment


def generate_simple_report(allure_results_dir, env, report_path):
    # 1. 解析 allure-results 中的测试结果
    total = 0
    passed = 0
    failed = 0
    skipped = 0
    cases = []

    for root, dirs, files in os.walk(allure_results_dir):
        for file in files:
            if file.endswith(".json") and "result" in file:
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    total += 1
                    # 统计结果
                    status = data.get("status", "unknown").upper()
                    if status == "PASSED":
                        passed += 1
                    elif status == "FAILED":
                        failed += 1
                    elif status == "SKIPPED":
                        skipped += 1
                    # 提取用例信息（含执行时间，用于排序）
                    case_name = data.get("name", "未知用例")
                    module = data.get("labels", [{}])[0].get("value", "未分类")
                    # 毫秒转秒，保留2位小数（修复耗时精度问题）
                    duration = round(data.get("duration", 0) / 1000, 3)
                    # 提取执行时间戳（Allure 记录的开始时间，用于排序）
                    start_time = data.get("start", 0)
                    failure_msg = ""
                    if status == "FAILED":
                        failure_msg = data.get("statusDetails", {}).get("message", "")[:50]  # 截取前50字
                    cases.append({
                        "module": module,
                        "case_name": case_name,
                        "status": status,
                        "duration": f"{duration}s",
                        "failure_msg": failure_msg or "-",
                        "start_time": start_time  # 执行时间戳，核心排序依据
                    })

    # 2. 核心优化：先按模块分组，再按执行时间排序（保证同一模块内顺序正确）
    module_cases = defaultdict(list)
    for case in cases:
        module_cases[case["module"]].append(case)  # 按模块分组

    sorted_cases = []
    for module, case_list in module_cases.items():
        # 每个模块内的用例按执行时间升序排序（先执行的在前）
        case_list.sort(key=lambda x: x["start_time"])
        sorted_cases.extend(case_list)  # 合并所有排序后的用例

    cases = sorted_cases  # 替换为排序后的用例列表

    # 3. 计算通过率
    pass_rate = round((passed / total) * 100, 2) if total > 0 else 0

    # 4. 动态获取BaseURL
    base_url = ENV_CONFIG[Environment[env.upper()]]['base_url']

    # 5. 生成报告内容（标题居中+动态BaseURL）
    report_content = f"""
<div align="center"><h1>自研跟单1.5.0接口自动化测试报告</h1></div>

## 1. 测试概览
| 项目名称       | VPS接口自动化测试                               |
|--------------|-----------------------------------------------|
| 执行时间       | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}|
| 执行环境       | {env}                                         |
| 总用例数       | {total}                                       |
| 通过数         | {passed}                                      |
| 失败数         | {failed}                                      |
| 跳过数         | {skipped}                                     |
| 通过率         | {pass_rate}%                                  |

## 2. 用例执行详情
| 模块          | 用例名称                | 执行结果   | 耗时    | 备注（失败原因）        |
|--------------|------------------------|----------|--------|-----------------------|
"""
    for case in cases:
        report_content += f"| {case['module']} | {case['case_name']} | {case['status']} | {case['duration']} | {case['failure_msg']} |\n"

    report_content += f"""
## 3. 环境信息
| 环境项         | 值                     |
|---------------|------------------------|
| Python版本     | 3.8.5                  |
| Pytest版本     | 7.4.3                  |
| Allure版本     | 2.14.2                 |
| 接口BaseURL    | {base_url}             |
| 测试设备        | Windows 11             |

## 4. 注意事项
1. 失败用例请查看“log”日志中的原因，优先排查接口返回数据或校验逻辑；
2. 报告生成路径：{os.path.abspath(report_path)}
"""

    # 6. 写入文件
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"基础版报告已生成：{report_path}")
