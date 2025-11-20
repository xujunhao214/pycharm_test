import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from collections import defaultdict
from lingkuanMT5_1029.config import ENV_CONFIG, Environment
from lingkuanMT5_1029.VAR.VAR import *
from datetime import datetime


def generate_simple_report(allure_results_dir, env, report_path):
    # 1. 从 Allure 结果中提取用例：按「用例唯一标识+参数」去重，保留最后一次执行结果（解决重试重复统计）
    case_final_results = {}  # key: 用例唯一标识（fullName+参数），value: 最后一次执行结果
    start_time_ts = None  # 所有用例的最早开始时间
    end_time_ts = None  # 所有用例的最晚结束时间

    # 遍历 Allure 结果文件
    for root, dirs, files in os.walk(allure_results_dir):
        for file in files:
            if file.endswith(".json") and "result" in file:
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    # 提取用例唯一标识（fullName + 参数，确保参数化用例不重复，重试用例能去重）
                    case_fullname = data.get("fullName", data.get("name", "未知用例"))
                    parameters = data.get("parameters", [])
                    param_str = "_".join([f"{p['name']}={p['value']}" for p in parameters])
                    case_unique_id = f"{case_fullname}_{param_str}" if param_str else case_fullname

                    # 提取用例执行时间（用于计算整体耗时）
                    case_start = data.get("start", 0)
                    case_stop = data.get("stop", 0)
                    if not start_time_ts or case_start < start_time_ts:
                        start_time_ts = case_start
                    if not end_time_ts or case_stop > end_time_ts:
                        end_time_ts = case_stop

                    # 状态映射：BROKEN → FAILED，统一状态标识
                    status = data.get("status", "unknown").upper()
                    if status == "BROKEN":
                        final_status = "FAILED"
                    elif status in ["PASSED", "FAILED", "SKIPPED"]:
                        final_status = status
                    else:
                        final_status = "FAILED"

                    # 提取模块（feature）、场景（story）
                    module = "未分类"
                    scenario = None
                    labels = data.get("labels", [])
                    for label in labels:
                        if label.get("name") == "feature":
                            module = label.get("value", "未分类")
                        elif label.get("name") == "story":
                            scenario_val = label.get("value", "").strip()
                            scenario = scenario_val if scenario_val else None

                    # 提取失败原因（仅 FAILED 状态）
                    failure_msg = "-"
                    if final_status == "FAILED":
                        failure_msg = data.get("statusDetails", {}).get("message", "")[:80] or "无详细原因"

                    # 保存最后一次执行结果（重试用例后执行的会覆盖先执行的，自动去重）
                    case_final_results[case_unique_id] = {
                        "case_name": data.get("name", "未知用例"),
                        "module": module,
                        "scenario": scenario,
                        "status": final_status,
                        "failure_msg": failure_msg,
                        "start_time": case_start
                    }

    # 2. 基于去重后的最终结果，进行统计计算（重试已去重，参数化用例正常统计）
    total = len(case_final_results)  # 总用例数（去重后：1个用例+1组参数=1条，重试仅保留1条）
    passed = 0
    failed = 0
    skipped = 0
    cases = []
    failed_cases = []

    for case_data in case_final_results.values():
        cases.append(case_data)
        status = case_data["status"]

        # 全局统计计数
        if status == "PASSED":
            passed += 1
        elif status == "FAILED":
            failed += 1
            failed_cases.append(case_data)
        elif status == "SKIPPED":
            skipped += 1

    # 3. 时间格式处理与总耗时计算（保持不变）
    def timestamp_to_str(ts):
        if not ts or ts == 0:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S")  # Allure时间戳是毫秒级

    start_time = timestamp_to_str(start_time_ts)
    end_time = timestamp_to_str(end_time_ts)

    if start_time_ts and end_time_ts:
        total_seconds = (end_time_ts - start_time_ts) / 1000
        hours = int(total_seconds // 3600)
        remaining_seconds = total_seconds % 3600
        minutes = int(remaining_seconds // 60)
        seconds = int(remaining_seconds % 60)
        if hours > 0:
            duration = f"{hours}时{minutes:02d}分{seconds:02d}秒"
        else:
            duration = f"{minutes}分{seconds:02d}秒"
    else:
        duration = "未知"

    # 全局通过率（避免除零）
    executed_total = total - skipped
    global_pass_rate = round((passed / executed_total) * 100, 2) if executed_total > 0 else 0.0

    # 4. 按模块分组统计（保持不变）
    module_stats = defaultdict(lambda: {
        "total": 0,  # 模块总用例数（去重后）
        "executed": 0,  # 模块实际执行数（排除跳过）
        "passed": 0,  # 模块通过数
        "failed": 0,  # 模块失败数
        "skipped": 0,  # 模块跳过数
        "pass_rate": 0.0  # 模块通过率
    })

    for case in cases:
        module = case["module"]
        status = case["status"]

        # 模块级数据累加
        module_stats[module]["total"] += 1
        if status == "SKIPPED":
            module_stats[module]["skipped"] += 1
        else:
            module_stats[module]["executed"] += 1
            if status == "PASSED":
                module_stats[module]["passed"] += 1
            else:
                module_stats[module]["failed"] += 1

        # 模块通过率计算（避免除零）
        if module_stats[module]["executed"] > 0:
            module_stats[module]["pass_rate"] = round(
                (module_stats[module]["passed"] / module_stats[module]["executed"]) * 100,
                2
            )
        else:
            module_stats[module]["pass_rate"] = 0.0

    # 5. 失败用例排序（保持不变）
    failed_cases.sort(key=lambda x: (x["module"], x["scenario"] or "", x["case_name"]))

    # 6. 动态确定项目名称（保持不变）
    if "cloud_results" in allure_results_dir:
        project_name = "Cloud"
        report_title = f"{PROJECT_NAME} 云策略接口自动化测试报告"
    elif "vps_results" in allure_results_dir:
        project_name = "VPS"
        report_title = f"{PROJECT_NAME} VPS接口自动化测试报告"
    elif "merged_allure-results" in allure_results_dir:
        project_name = "VPS+云策略汇总"
        report_title = f"{PROJECT_NAME}接口自动化汇总测试报告"
    else:
        project_name = "未知项目"
        report_title = f"{PROJECT_NAME}接口自动化测试报告"

    # 7. 动态获取BaseURL（保持不变）
    try:
        base_url = ENV_CONFIG[Environment[env.upper()]]['base_url']
    except (KeyError, ValueError):
        base_url = "未知环境URL"

    # 8. 生成报告内容（保持不变）
    report_content = f"""
<div align="center"><h1>{report_title}</h1></div>

## 1. 测试概览
| 项目名称       | {project_name}接口自动化测试                               |
|--------------|----------------------------------------------------------|
| 开始时间       | {start_time}                                              |
| 结束时间       | {end_time}                                                |
| 总耗时         | {duration}                                                |
| 执行环境       | {env}                                                    |
| 总用例数       | {total}                                                  |
| 实际执行数     | {executed_total}                                          |
| 通过数（PASSED）| {passed}                                                  |
| 失败数（FAILED）| {failed}                                                  |
| 跳过数（SKIPPED）| {skipped}                                                |
| 整体通过率     | {global_pass_rate:.2f}%                                   |
"""

    # 9. 模块统计列表（保持不变）
    report_content += f"""
## 2. 模块统计列表
| 模块                 | 总用例数  | 实际执行数   | 通过数   | 失败数  | 跳过数  | 通过率   |
|---------------------|----------|------------|--------|--------|--------|----------|
"""
    for module in sorted(module_stats.keys()):
        stats = module_stats[module]
        report_content += (
            f"| {module} | {stats['total']} | {stats['executed']} | "
            f"{stats['passed']} | {stats['failed']} | {stats['skipped']} | "
            f"{stats['pass_rate']:.2f}% |\n"
        )

    # 10. 失败用例列表（保持不变）
    report_content += f"""
## 3. 失败用例列表（共{len(failed_cases)}条）
| 模块                | 场景                          | 用例名称                | 执行结果   | 备注（失败原因）          |
|---------------------|-----------------------------|------------------------|----------|-------------------------|
"""
    if failed_cases:
        for fail_case in failed_cases:
            scenario_val = fail_case["scenario"] if fail_case["scenario"] is not None else "-"
            case_name = fail_case["case_name"][:60] + "..." if len(fail_case["case_name"]) > 60 else fail_case[
                "case_name"]
            report_content += (
                f"| {fail_case['module']} | {scenario_val} | {case_name} | "
                f"{fail_case['status']} | {fail_case['failure_msg']} |\n"
            )
    else:
        report_content += "| - | - | - | - | 无失败/中断用例 |\n"

    report_content += f"""
## 4. 环境信息
| 环境项         | 值                     |
|---------------|------------------------|
| Python版本     | 3.8.5                  |
| Pytest版本     | 7.4.3                  |
| Allure版本     | 2.14.2                 |
| 接口BaseURL    | {base_url}             |
| 测试设备        | Windows 11             |

## 5. 注意事项
1. 支持重试用例去重：同一用例（含参数化）多次重试仅保留最后一次结果，重试成功不计入失败；
2. 失败用例包含原FAILED和BROKEN状态，参数化用例按独立用例统计；
3. 通过率计算规则：通过率=通过数/实际执行数（排除跳过用例），保留2位小数；
4. 报告生成路径：{os.path.abspath(report_path)}
"""

    # 11. 写入报告文件（保持不变）
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(
        f"简化版报告已生成：{report_path}\n"
        f"全局统计：共{total}条用例，实际执行{executed_total}条，失败{failed}条，跳过{skipped}条，整体通过率：{global_pass_rate:.2f}%\n"
        f"涉及模块数：{len(module_stats)}个"
    )


if __name__ == "__main__":
    generate_simple_report(
        allure_results_dir="report/cloud_results",
        env="test",
        report_path="report/Cloud接口自动化测试报告.md"
    )
