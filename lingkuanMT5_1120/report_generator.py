import json
import sys
import os

# 新增：添加项目根目录到Python路径（解决Jenkins导入问题）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from collections import defaultdict
from lingkuanMT5_1120.config import ENV_CONFIG, Environment
from VAR.VAR import *
from datetime import datetime


def generate_simple_report(allure_results_dir, env, report_path):
    # 1. 先收集所有用例结果（含重试），不做去重
    all_case_results = []  # 存储所有用例结果（含重试）
    start_time_ts = None
    end_time_ts = None

    for root, dirs, files in os.walk(allure_results_dir):
        for file in files:
            if file.endswith(".json") and "result" in file:
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    # 生成用例唯一标识（与之前一致）
                    case_fullname = data.get("fullName", data.get("name", "未知用例"))
                    case_stage = data.get("stage", "call").upper()
                    parameters = data.get("parameters", [])
                    param_str = json.dumps(parameters, ensure_ascii=False, sort_keys=True)
                    case_unique_id = f"{case_fullname}_{case_stage}_{param_str}"

                    # 提取执行时间（重点：记录 stop 时间，用于排序）
                    case_start = data.get("start", 0)
                    case_stop = data.get("stop", 0)
                    if not start_time_ts or case_start < start_time_ts:
                        start_time_ts = case_start
                    if not end_time_ts or case_stop > end_time_ts:
                        end_time_ts = case_stop

                    # 状态映射、模块、场景、失败原因提取（与之前一致）
                    status = data.get("status", "unknown").upper()
                    final_status = "FAILED" if status == "BROKEN" else status if status in ["PASSED", "FAILED",
                                                                                            "SKIPPED"] else "FAILED"
                    module = "未分类"
                    scenario = None
                    labels = data.get("labels", [])
                    for label in labels:
                        if label.get("name") == "feature":
                            module = label.get("value", "未分类")
                        elif label.get("name") == "story":
                            scenario_val = label.get("value", "").strip()
                            scenario = scenario_val if scenario_val else None
                    failure_msg = data.get("statusDetails", {}).get("message", "")[
                                  :80] or "无详细原因" if final_status == "FAILED" else "-"

                    # 保存所有信息（含 stop 时间）
                    all_case_results.append({
                        "case_unique_id": case_unique_id,
                        "case_name": data.get("name", "未知用例"),
                        "module": module,
                        "scenario": scenario,
                        "status": final_status,
                        "failure_msg": failure_msg,
                        "start_time": case_start,
                        "stop_time": case_stop  # 关键：用于排序，取最后一次执行结果
                    })

    # 2. 按 case_unique_id 分组，每组内按 stop_time 降序排序，保留最后一次结果
    case_groups = defaultdict(list)
    for case in all_case_results:
        case_groups[case["case_unique_id"]].append(case)

    # 去重：每组取最后一次执行（stop_time 最大）的结果
    case_final_results = {}
    for case_id, cases in case_groups.items():
        # 按 stop_time 降序排序，第一个就是最后一次执行的结果
        cases_sorted = sorted(cases, key=lambda x: x["stop_time"], reverse=True)
        case_final_results[case_id] = cases_sorted[0]

    # 3. 统计计算（基于去重后的结果）
    total = len(case_final_results)
    passed = 0
    failed = 0
    skipped = 0
    cases = []
    failed_cases = []

    for case_data in case_final_results.values():
        cases.append(case_data)
        status = case_data["status"]
        if status == "PASSED":
            passed += 1
        elif status == "FAILED":
            failed += 1
            failed_cases.append(case_data)
        elif status == "SKIPPED":
            skipped += 1

    # 4. 后续逻辑（时间格式、模块统计、报告生成）完全不变
    def timestamp_to_str(ts):
        if not ts or ts == 0:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S")

    start_time = timestamp_to_str(start_time_ts)
    end_time = timestamp_to_str(end_time_ts)
    if start_time_ts and end_time_ts:
        total_seconds = (end_time_ts - start_time_ts) / 1000
        hours = int(total_seconds // 3600)
        remaining_seconds = total_seconds % 3600
        minutes = int(remaining_seconds // 60)
        seconds = int(remaining_seconds % 60)
        duration = f"{hours}时{minutes:02d}分{seconds:02d}秒" if hours > 0 else f"{minutes}分{seconds:02d}秒"
    else:
        duration = "未知"
    executed_total = total - skipped
    global_pass_rate = round((passed / executed_total) * 100, 2) if executed_total > 0 else 0.0

    module_stats = defaultdict(
        lambda: {"total": 0, "executed": 0, "passed": 0, "failed": 0, "skipped": 0, "pass_rate": 0.0})
    for case in cases:
        module = case["module"]
        status = case["status"]
        module_stats[module]["total"] += 1
        if status == "SKIPPED":
            module_stats[module]["skipped"] += 1
        else:
            module_stats[module]["executed"] += 1
            if status == "PASSED":
                module_stats[module]["passed"] += 1
            else:
                module_stats[module]["failed"] += 1
        if module_stats[module]["executed"] > 0:
            module_stats[module]["pass_rate"] = round(
                (module_stats[module]["passed"] / module_stats[module]["executed"]) * 100, 2)
        else:
            module_stats[module]["pass_rate"] = 0.0

    failed_cases.sort(key=lambda x: (x["module"], x["scenario"] or "", x["case_name"]))

    # 项目名称与报告标题
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

    # 环境信息
    try:
        base_url = ENV_CONFIG[Environment[env.upper()]]['base_url']
    except (KeyError, ValueError):
        base_url = "未知环境URL"

    # 生成报告内容
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
1. 重试用例去重：按执行时间排序，保留最后一次执行结果，重试成功不计入失败；
2. 参数化用例独立统计：不同参数的用例视为独立条目，确保统计准确；
3. 通过率计算规则：通过率=通过数/实际执行数（排除跳过用例），保留2位小数；
4. 报告生成路径：{os.path.abspath(report_path)}
"""

    # 写入报告文件
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
