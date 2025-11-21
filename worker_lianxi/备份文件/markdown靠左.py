import json
import sys
import os
import re
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import markdown  # 导入markdown库
from collections import defaultdict
from lingkuanMT5_1120.config import ENV_CONFIG, Environment
from VAR.VAR import *
from datetime import datetime

# 兼容CompareOp枚举
try:
    from enum import Enum


    class CompareOp(Enum):
        EQ = "等于"
        NE = "不等于"
        GT = "大于"
        LT = "小于"
        GE = "大于等于"
        LE = "小于等于"
        IN = "包含于"
        NOT_IN = "不包含于"
except:
    pass


def generate_simple_report(allure_results_dir, env, report_path):
    # 1. 收集用例结果（精准适配最新detail_msg格式）
    all_case_results = []
    start_time_ts = None
    end_time_ts = None

    for root, dirs, files in os.walk(allure_results_dir):
        for file in files:
            if file.endswith(".json") and "result" in file:
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    # 生成用例唯一标识
                    case_fullname = data.get("fullName", data.get("name", "未知用例"))
                    case_stage = data.get("stage", "call").upper()
                    parameters = data.get("parameters", [])
                    param_str = json.dumps(parameters, ensure_ascii=False, sort_keys=True)
                    case_unique_id = f"{case_fullname}_{case_stage}_{param_str}"

                    # 提取执行时间
                    case_start = data.get("start", 0)
                    case_stop = data.get("stop", 0)
                    if not start_time_ts or case_start < start_time_ts:
                        start_time_ts = case_start
                    if not end_time_ts or case_stop > end_time_ts:
                        end_time_ts = case_stop

                    # 状态映射、模块、场景提取
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

                    # -------------------------- 核心修改：区分失败场景（数据库超时/JSON断言） --------------------------
                    status_details = data.get("statusDetails", {})
                    failure_msg = "-"  # 备注（失败原因）
                    specific_reason = "-"  # 具体原因（实际/预期）

                    # -------------------------- 核心修改：完整区分失败场景（超时/JSON断言/其他） --------------------------
                    status_details = data.get("statusDetails", {})
                    failure_msg = "-"  # 备注（失败原因）
                    specific_reason = "-"  # 具体原因（实际/预期）

                    if final_status == "FAILED":
                        msg = status_details.get("message", "")
                        trace = status_details.get("trace", "")

                        # 场景1：数据库超时（关键词匹配 TimeoutError + 等待记录/删除）
                        if "TimeoutError" in trace and ("等待记录" in msg or "删除" in msg):
                            # 备注：显示完整超时信息（如“等待记录出现超时（30秒）”）
                            failure_msg = msg.strip()[:80]
                            # 具体原因：为空
                            specific_reason = ""

                        # 场景2：JSON断言失败（关键词匹配 AssertionError + 响应字段/JSON路径）
                        elif "AssertionError" in trace and ("JSON路径" in msg or "响应" in msg):
                            # 提取“备注（失败原因）”：仅显示错误描述（如“响应msg字段应为success”）
                            json_match = re.search(r'Failed: ([^（]+)', msg)  # 匹配“Failed: xxx”到“（”之前的内容
                            if json_match:
                                failure_msg = json_match.group(1).strip()[:80]
                            else:
                                failure_msg = "响应字段断言失败"

                            # 提取“具体原因（实际/预期）”：匹配“预期: xxx, 实际: xxx”（兼容末尾是否有括号）
                            # 适配两种格式：1. "预期: a, 实际: b"  2. "预期: a, 实际: b）"
                            actual_expected_match = re.search(r'预期: (.*?), 实际: (.*?)(?:）|$)', msg)
                            if actual_expected_match:
                                expected_val = actual_expected_match.group(1).strip()
                                actual_val = actual_expected_match.group(2).strip()
                                specific_reason = f"实际: {actual_val}，预期: {expected_val}"
                            else:
                                specific_reason = "未获取到实际/预期信息"

                        # 场景3：其他失败（如verify_data校验、普通断言等）
                        else:
                            # 保持原有逻辑，提取校验失败信息
                            failure_match = re.search(r'校验失败: ([^|]+) \| 实际:', msg)
                            if failure_match:
                                failure_msg = failure_match.group(1).strip()[:80]
                            else:
                                failure_msg = msg[:80] or "无详细原因"

                            # 提取实际/预期
                            actual_match = re.search(r'实际: ([^|]+)', msg)
                            expected_match = re.search(r'预期: ([^|]+)', msg)
                            if actual_match and expected_match:
                                actual_val = actual_match.group(1).strip()
                                expected_val = expected_match.group(1).strip()
                                specific_reason = f"实际: {actual_val}，预期: {expected_val}"
                            else:
                                specific_reason = "未获取到实际/预期信息"

                    all_case_results.append({
                        "case_unique_id": case_unique_id,
                        "case_name": data.get("name", "未知用例"),
                        "module": module,
                        "scenario": scenario,
                        "status": final_status,
                        "failure_msg": failure_msg,
                        "specific_reason": specific_reason,
                        "start_time": case_start,
                        "stop_time": case_stop
                    })

    # 2. 用例去重（逻辑不变）
    case_groups = defaultdict(list)
    for case in all_case_results:
        case_groups[case["case_unique_id"]].append(case)
    case_final_results = {}
    for case_id, cases in case_groups.items():
        cases_sorted = sorted(cases, key=lambda x: x["stop_time"], reverse=True)
        case_final_results[case_id] = cases_sorted[0]

    # 3. 统计计算（逻辑不变）
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

    # 时间格式转换（逻辑不变）
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

    # 模块统计（逻辑不变）
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

    # 项目名称与报告标题（逻辑不变）
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

    # 环境信息（逻辑不变）
    try:
        base_url = ENV_CONFIG[Environment[env.upper()]]['base_url']
    except (KeyError, ValueError):
        base_url = "未知环境URL"

    # 生成Markdown报告（确保字段正确映射）
    report_content = f"""# {report_title}

## 1. 测试概览
| 项目名称       | {project_name}接口自动化测试 |
|--------------|--------------------------|
| 开始时间       | {start_time}              |
| 结束时间       | {end_time}                |
| 总耗时         | {duration}                |
| 执行环境       | {env}                    |
| 总用例数       | {total}                  |
| 实际执行数     | {executed_total}          |
| 通过数（PASSED）| {passed}                  |
| 失败数（FAILED）| {failed}                  |
| 跳过数（SKIPPED）| {skipped}                |
| 整体通过率     | {global_pass_rate:.2f}%   |

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

    # 失败用例列表（字段精准对应）
    report_content += f"""
## 3. 失败用例列表（共{len(failed_cases)}条）
| 模块                | 场景                          | 用例名称                | 执行结果   | 备注（失败原因）          | 具体原因（实际/预期）      |
|---------------------|-----------------------------|------------------------|----------|-------------------------|-------------------------|
"""
    if failed_cases:
        for fail_case in failed_cases:
            scenario_val = fail_case["scenario"] if fail_case["scenario"] is not None else "-"
            case_name = fail_case["case_name"][:60] + "..." if len(fail_case["case_name"]) > 60 else fail_case[
                "case_name"]
            report_content += (
                f"| {fail_case['module']} | {scenario_val} | {case_name} | "
                f"{fail_case['status']} | {fail_case['failure_msg']} | {fail_case['specific_reason']} |\n"
            )
    else:
        report_content += "| - | - | - | - | 无失败用例 | - |\n"

    report_content += f"""
## 4. 环境信息
| 环境项         | 值                     |
|---------------|------------------------|
| Python版本     | 3.8.5                  |
| Pytest版本     | 7.4.3                  |
| Allure版本     | 2.14.2                 |
| 接口BaseURL    | {base_url}             |

## 5. 注意事项
1. 通过率计算规则：仅统计实际执行的用例（排除跳过用例）；
2. 失败用例请查看"备注"和"具体原因"，实际操作步骤请查看Allure报告的日志文件，优先排查接口返回数据、校验逻辑；

"""
# 报告生成路径：{os.path.abspath(report_path)}

    # 写入MD报告
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(
        f"简化版 MD 报告已生成：{report_path}\n"
        f"全局统计：共{total}条用例，实际执行{executed_total}条，失败{failed}条，跳过{skipped}条，整体通过率：{global_pass_rate:.2f}%\n"
        f"涉及模块数：{len(module_stats)}个"
    )

    # 生成HTML报告（表格靠左对齐）
    html_report_path = report_path.replace(".md", ".html")

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        html_content = markdown.markdown(
            md_content,
            extensions=[
                "extra",  # 支持表格
                "sane_lists",  # 修复列表渲染
                "nl2br"  # 换行符转<br>
            ]
        )

        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: "Microsoft YaHei", Arial, sans-serif;
        }}
        body {{
            background-color: #fff;
            color: #333;
            line-height: 1.6;
            padding: 30px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 24px;
            color: #333;
            text-align: center;
            margin: 20px 0 30px;
            padding-bottom: 10px;
            border-bottom: 1px solid #ddd;
        }}
        h2 {{
            font-size: 20px;
            color: #333;
            margin: 30px 0 15px;
            padding-left: 5px;
            border-left: 3px solid #3498db;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            border: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
            padding: 10px 12px;
            text-align: left;
            font-weight: bold;
            border: 1px solid #ddd;
        }}
        td {{
            padding: 10px 12px;
            border: 1px solid #ddd;
            text-align: left;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #f0f7ff;
        }}
        .notes {{
            margin: 15px 0;
            padding: 10px;
            background-color: #f9f9f9;
            border-left: 3px solid #ddd;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>
"""

        with open(html_report_path, "w", encoding="utf-8") as f:
            f.write(html_template)
        print(f"HTML 报告已生成：{html_report_path}")
        print(f"HTML 报告绝对路径：{os.path.abspath(html_report_path)}")

    except ImportError as e:
        print(f"MD 转 HTML 失败！缺少依赖：{str(e)}")
        print("请执行以下命令安装依赖：pip install markdown pygments")
    except Exception as e:
        print(f"MD 转 HTML 失败！错误信息：{str(e)}")


# 兼容verify_data函数（你的最新版本，避免导入报错）
try:
    import allure
    import pytest
    import logging


    def verify_data(
            self,
            actual_value,
            expected_value,
            op: CompareOp,
            message: str,
            attachment_name: str,
            attachment_type="text/plain",
            use_isclose=True,
            rel_tol=1e-9,
            abs_tol=0
    ):
        """
        通用数据校验函数，支持浮点容错比较
        :param actual_value: 实际值
        :param expected_value: 预期值
        :param op: 比较操作，CompareOp 枚举
        :param message: 校验失败时的提示信息
        :param attachment_name: Allure 附件名称
        :param attachment_type: Allure 附件类型，默认文本
        :param use_isclose: 是否使用math.isclose进行浮点容错比较
        :param rel_tol: 相对容差（默认1e-9）
        :param abs_tol: 绝对容差（默认0.0）
        其他参数同前
        """
        with allure.step(f"校验: {message}"):
            result = False
            try:
                # 处理浮点容错比较（仅对EQ/NE操作生效）
                if use_isclose and op in (CompareOp.EQ, CompareOp.NE):
                    if not (isinstance(actual_value, (int, float)) and
                            isinstance(expected_value, (int, float))):
                        # 非数字类型自动禁用isclose，避免报错
                        use_isclose = False
                        logging.warning(f"自动禁用isclose：非数字类型比较（实际值类型：{type(actual_value)}）")

                    # 计算isclose结果
                    is_close = math.isclose(
                        actual_value,
                        expected_value,
                        rel_tol=rel_tol,
                        abs_tol=abs_tol
                    )
                    # 根据操作类型取反
                    result = is_close if op == CompareOp.EQ else not is_close

                # 普通比较逻辑
                else:
                    if op == CompareOp.EQ:
                        result = actual_value == expected_value
                    elif op == CompareOp.NE:
                        result = actual_value != expected_value
                    elif op == CompareOp.GT:
                        result = actual_value > expected_value
                    elif op == CompareOp.LT:
                        result = actual_value < expected_value
                    elif op == CompareOp.GE:
                        result = actual_value >= expected_value
                    elif op == CompareOp.LE:
                        result = actual_value <= expected_value
                    elif op == CompareOp.IN:
                        result = actual_value in expected_value
                    elif op == CompareOp.NOT_IN:
                        result = actual_value not in expected_value

            except TypeError as e:
                # 类型错误提示：移除换行，精简格式
                err_msg = f"校验类型错误: {str(e)} | 实际值类型: {type(actual_value)} | 预期值类型: {type(expected_value)}"
                pytest.fail(err_msg)

            # 生成详细提示信息（移除换行符，用 | 分隔，避免表格错乱）
            # 若值过长，可截取前50字符（根据需要调整）
            def truncate(val):
                val_str = str(val)
                return val_str[:50] + "..." if len(val_str) > 50 else val_str

            detail_msg = (
                f"实际: {truncate(actual_value)} | "
                f"操作: {op.value} | "
                f"预期: {truncate(expected_value)}"
            )

            # 生成Allure附件（保留完整信息，不影响原始报告）
            full_detail = (
                f"校验场景: {message}\n"
                f"实际值: {actual_value}\n"
                f"比较操作: {op.value}\n"
                f"预期值: {expected_value}\n"
                # f"容差设置(rel/abs): {rel_tol}/{abs_tol}\n"
                f"是否通过: {'是' if result else '否'}"
            )

            # 添加allure.attach，将完整信息写入Allure报告（不影响简化版报告）
            allure.attach(
                full_detail,  # 附件内容（完整信息）
                name=attachment_name,  # 附件名称（来自参数）
                attachment_type=attachment_type  # 附件类型
            )

            if not result:
                # 失败提示：合并message和detail_msg，无换行
                pytest.fail(f"校验失败: {message} | {detail_msg}")
            logging.info(f"校验通过: {message} | {detail_msg}")
except:
    pass

if __name__ == "__main__":
    generate_simple_report(
        allure_results_dir="report/cloud_results",
        env="test",
        report_path="report/Cloud接口自动化测试报告.md"
    )
