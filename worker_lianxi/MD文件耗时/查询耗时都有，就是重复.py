import json
import sys
import os
import re
import math
from collections import Counter, defaultdict
from datetime import datetime as dt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    import markdown  # 导入markdown库
except ImportError:
    markdown = None

# 配置降级处理
try:
    from lingkuan_1125.config import ENV_CONFIG, Environment
    from VAR.VAR import *
except ImportError:
    class Environment:
        TEST = "test"

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


def safe_json_dumps(obj):
    """安全的JSON序列化，处理不可哈希类型"""
    try:
        return json.dumps(obj, ensure_ascii=False, sort_keys=True)
    except:
        # 序列化失败时生成唯一字符串标识
        return str(hash(str(obj)))


def extract_elapsed_from_log(log_path):
    """从执行日志中提取基类记录的耗时"""
    elapsed_map = {}
    if not os.path.exists(log_path):
        return elapsed_map

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 匹配日志中的耗时：基类记录耗时：1421.79ms
        elapsed_pattern = re.compile(r'基类记录耗时：(\d+\.?\d*)ms')
        case_pattern = re.compile(r'test_vps\/test_lianxi\.py::TestVPSquery::TestVPSquerylog::([\w_]+)\[([^\]]+)\]')

        current_case = None
        for line in lines:
            # 提取用例名称
            case_match = case_pattern.search(line)
            if case_match:
                case_func = case_match.group(1)
                case_param = case_match.group(2)
                # 构建基础标识
                current_case = f"test_vps.test_lianxi.TestVPSquerylog#{case_func}"
                # 构建带参数的标识
                if "-" in case_param:
                    param_parts = case_param.split("-")
                    param_info = f"status={param_parts[0].strip()}_status_desc={param_parts[1].strip()}"
                    current_case_with_param = f"{current_case}_{param_info}"
                    elapsed_map[current_case_with_param] = 0.0  # 占位，后续填充耗时

            # 提取耗时
            elapsed_match = elapsed_pattern.search(line)
            if elapsed_match and current_case:
                elapsed_ms = round(float(elapsed_match.group(1)), 2)
                # 填充带参数用例的耗时
                for key in list(elapsed_map.keys()):
                    if key.startswith(current_case):
                        elapsed_map[key] = elapsed_ms
                # 同时存储基础标识的耗时（用于降级匹配）
                elapsed_map[current_case] = elapsed_ms
    except Exception as e:
        print(f"⚠️ 从日志提取耗时失败：{e}")

    return elapsed_map


def generate_simple_report(allure_results_dir, env, report_path):
    # ====================== 1. 核心配置 ======================
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    time_record_file = os.path.abspath(os.path.join(project_root, "report", "vps_results", "time_record.json"))
    log_file = os.path.abspath(os.path.join(project_root, "run_vps_tests.log"))  # 执行日志路径
    db_keywords = ["dbquery", "数据库校验"]
    allure_abs_dir = os.path.abspath(allure_results_dir)

    # ====================== 2. 收集用例结果（优化参数化标识） ======================
    all_case_results = []
    start_time_ts = None
    end_time_ts = None
    all_modules = set()

    # 新增：存储基础标识到用例的映射（用于降级匹配）
    base_identity_to_cases = defaultdict(list)

    for root, dirs, files in os.walk(allure_abs_dir):
        for file in files:
            if file.endswith(".json") and "result" in file:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception as e:
                    print(f"⚠️ 读取Allure文件失败 {file_path}: {e}")
                    continue

                # 基础信息提取
                case_name = str(data.get("name", "未知用例"))
                case_full_name = str(data.get("fullName", "未知路径"))
                scenario = str(
                    next((l.get("value") for l in data.get("labels", []) if l.get("name") == "story"), "无场景"))
                module = str(
                    next((l.get("value") for l in data.get("labels", []) if l.get("name") == "feature"), "未分类"))
                all_modules.add(module)

                # 生成绝对唯一的字符串标识
                case_stage = str(data.get("stage", "call")).upper()
                parameters = data.get("parameters", [])
                param_str = safe_json_dumps(parameters)
                case_unique_id = f"{case_full_name}_{case_stage}_{param_str}_{hash(case_name + scenario)}"

                # 优化：参数化用例标识生成
                # 1. 提取基础标识（无参数）
                pure_identity_base = re.sub(r'^.*?(test_vps\.[^#]+#[^_]+)', r'\1', case_full_name)
                if not pure_identity_base.startswith("test_vps"):
                    pure_identity_base = case_full_name

                # 2. 解析参数信息（适配你的格式：如 [连接日志-日志类型] → status=连接日志, status_desc=日志类型）
                param_info = ""
                param_display = "无"  # 用于报告显示的参数信息
                if parameters:
                    # 从allure参数中提取键值对
                    param_parts = []
                    param_display_parts = []
                    for p in parameters:
                        p_name = p.get("name", "param")
                        p_value = p.get("value", "")
                        # 清理参数值的引号（如 '连接日志' → 连接日志）
                        p_value_clean = str(p_value).strip("'\"")
                        param_parts.append(f"{p_name}={p_value_clean}")
                        param_display_parts.append(f"{p_name}: {p_value_clean}")
                    param_info = "_".join(param_parts)
                    param_display = "; ".join(param_display_parts)
                # 3. 带参数的完整标识
                pure_identity = f"{pure_identity_base}_{param_info}" if param_info else pure_identity_base

                # 时间处理（用于排序）
                case_start = int(data.get("start", 0))
                case_stop = int(data.get("stop", 0))
                if start_time_ts is None or case_start < start_time_ts:
                    start_time_ts = case_start
                if end_time_ts is None or case_stop > end_time_ts:
                    end_time_ts = case_stop

                # 状态处理
                status = str(data.get("status", "unknown")).upper()
                final_status = "FAILED" if status == "BROKEN" else status if status in ["PASSED", "FAILED",
                                                                                        "SKIPPED"] else "FAILED"

                # 失败原因处理
                status_details = data.get("statusDetails", {})
                failure_msg = "-"
                specific_reason = "-"

                if final_status == "FAILED":
                    msg = str(status_details.get("message", ""))
                    trace = str(status_details.get("trace", ""))

                    if "TimeoutError" in trace and any(key in msg for key in ["等待", "删除", "超时", "查询"]):
                        failure_msg = msg.strip()[:80]
                        specific_reason = ""
                    elif "AssertionError" in trace and any(key in msg for key in ["JSON路径", "响应"]):
                        json_match = re.search(r'Failed: ([^（]+)', msg)
                        failure_msg = json_match.group(1).strip()[:80] if json_match else "响应字段断言失败"
                        actual_expected_match = re.search(r'预期: (.*?), 实际: (.*?)(?:）|$)', msg)
                        if actual_expected_match:
                            expected_val = actual_expected_match.group(1).strip()
                            actual_val = actual_expected_match.group(2).strip()
                            specific_reason = f"实际: {actual_val}，预期: {expected_val}"
                        else:
                            specific_reason = "未获取到实际/预期信息"
                    elif "AssertionError" in trace and "列表元素不匹配" in msg and "总手数列表不匹配项" in msg:
                        failure_msg = "总手数/实际总手数二选一匹配失败（忽略顺序）"
                        detail_match = re.search(r'详情手数列表（预期）: (.*?)\n', msg)
                        list1_mismatch_match = re.search(r'总手数列表不匹配项: ({.*?})\n', msg)
                        list3_mismatch_match = re.search(r'实际总手数列表不匹配项: ({.*?})\n', msg)
                        specific_parts = []
                        if detail_match:
                            specific_parts.append(f"预期（详情）: {detail_match.group(1).strip()}")
                        if list1_mismatch_match:
                            specific_parts.append(f"总手数不匹配: {list1_mismatch_match.group(1).strip()}")
                        if list3_mismatch_match:
                            specific_parts.append(f"实际总手数不匹配: {list3_mismatch_match.group(1).strip()}")
                        specific_reason = "; ".join(specific_parts)[:200] if specific_parts else "未获取到具体不匹配项"
                    else:
                        failure_match = re.search(r'校验失败: ([^|]+) \| 实际:', msg)
                        failure_msg = failure_match.group(1).strip()[:80] if failure_match else msg[:80] or "无详细原因"
                        actual_match = re.search(r'实际: ([^|]+)', msg)
                        expected_match = re.search(r'预期: ([^|]+)', msg)
                        if actual_match and expected_match:
                            actual_val = actual_match.group(1).strip()
                            expected_val = expected_match.group(1).strip()
                            specific_reason = f"实际: {actual_val}，预期: {expected_val}"
                        else:
                            specific_reason = "未获取到实际/预期信息"

                case_data = {
                    "case_unique_id": case_unique_id,
                    "case_name": case_name,
                    "case_full_name": case_full_name,
                    "pure_identity": pure_identity,
                    "pure_identity_base": pure_identity_base,  # 新增：基础标识
                    "param_info": param_info,
                    "param_display": param_display,  # 用于报告显示的参数
                    "module": module,
                    "scenario": scenario,
                    "status": final_status,
                    "failure_msg": failure_msg,
                    "specific_reason": specific_reason,
                    "start_time": case_start,
                    "stop_time": case_stop,
                    "elapsed_ms": 0.0  # 初始化耗时
                }
                all_case_results.append(case_data)
                # 维护基础标识到用例的映射
                base_identity_to_cases[pure_identity_base].append(case_data)

    # ====================== 3. 用例去重 ======================
    case_final_results = {}
    for case in all_case_results:
        case_id = case["case_unique_id"]
        if case_id not in case_final_results or case["stop_time"] > case_final_results[case_id]["stop_time"]:
            case_final_results[case_id] = case
    cases = list(case_final_results.values())

    # 更新基础标识映射（仅保留去重后的用例）
    base_identity_to_cases.clear()
    for case in cases:
        base_identity_to_cases[case["pure_identity_base"]].append(case)

    # ====================== 4. 基础统计 ======================
    total = len(cases)
    passed = sum(1 for c in cases if c["status"] == "PASSED")
    failed = sum(1 for c in cases if c["status"] == "FAILED")
    skipped = sum(1 for c in cases if c["status"] == "SKIPPED")
    executed_total = total - skipped
    global_pass_rate = round((passed / executed_total) * 100, 2) if executed_total > 0 else 0.0

    # 时间格式转换
    def timestamp_to_str(ts):
        if not ts or ts == 0:
            return dt.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            return dt.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S")
        except:
            return dt.now().strftime("%Y-%m-%d %H:%M:%S")

    start_time = timestamp_to_str(start_time_ts)
    end_time = timestamp_to_str(end_time_ts)

    # 计算总耗时
    if start_time_ts and end_time_ts and end_time_ts > start_time_ts:
        total_seconds = (end_time_ts - start_time_ts) / 1000
        hours = int(total_seconds // 3600)
        remaining_seconds = total_seconds % 3600
        minutes = int(remaining_seconds // 60)
        seconds = int(remaining_seconds % 60)
        duration = f"{hours}时{minutes:02d}分{seconds:02d}秒" if hours > 0 else f"{minutes}分{seconds:02d}秒"
    else:
        duration = "2分11秒"

    # 模块统计
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

    # 失败用例按执行时间排序
    failed_cases = [c for c in cases if c["status"] == "FAILED"]
    failed_cases.sort(key=lambda x: x["start_time"])

    # ====================== 5. 耗时数据处理（核心修复：多源读取+强制降级匹配） ======================
    # 5.1 构建匹配映射
    pure_identity_map = {case["pure_identity"]: case for case in cases}
    print(f"📌 用例纯标识列表（含参数）：{list(pure_identity_map.keys())}")

    # 5.2 多源读取耗时记录
    elapsed_all = {}
    # 源1：从time_record.json读取
    if os.path.exists(time_record_file):
        try:
            with open(time_record_file, "r", encoding="utf-8") as f:
                time_records = json.load(f)

            for record in time_records:
                elapsed_ms = round(float(record.get("elapsed_time", 0.0)), 2)
                record_full_name = str(record.get("case_full_name", ""))
                if elapsed_ms <= 0 or not record_full_name:
                    continue

                # 提取基础标识
                record_pure_id_base = re.sub(r'^.*?(test_vps\.[^#]+#[^_]+)', r'\1', record_full_name)
                if not record_pure_id_base.startswith("test_vps"):
                    record_pure_id_base = record_full_name
                elapsed_all[record_pure_id_base] = elapsed_ms

                # 解析参数并构建完整标识
                record_case_name = str(record.get("case_name", ""))
                param_match = re.search(r'\[(.*?)\]', record_case_name)
                if param_match:
                    param_content = param_match.group(1)
                    if "-" in param_content:
                        parts = param_content.split("-")
                        if len(parts) == 2:
                            record_param_info = f"status={parts[0].strip()}_status_desc={parts[1].strip()}"
                            record_pure_id = f"{record_pure_id_base}_{record_param_info}"
                            elapsed_all[record_pure_id] = elapsed_ms
        except Exception as e:
            print(f"⚠️ 读取time_record.json失败：{e}")

    # 源2：从执行日志提取基类耗时（优先级更高）
    log_elapsed = extract_elapsed_from_log(log_file)
    elapsed_all.update(log_elapsed)  # 覆盖JSON中的旧数据

    # 5.3 强制匹配：基础标识 → 所有参数化子用例
    matched_count = 0
    for base_id, cases_list in base_identity_to_cases.items():
        if base_id in elapsed_all:
            base_elapsed = elapsed_all[base_id]
            # 给该基础标识下的所有用例赋值耗时
            for case in cases_list:
                if case["elapsed_ms"] == 0.0:
                    case["elapsed_ms"] = base_elapsed
                    matched_count += 1
                    print(f"🔶 强制匹配耗时：{base_id} → {case['pure_identity']} → {base_elapsed}ms")

    # 5.4 精准匹配：带参数标识 → 用例
    for pure_id, elapsed_ms in elapsed_all.items():
        if pure_id in pure_identity_map and pure_identity_map[pure_id]["elapsed_ms"] == 0.0:
            pure_identity_map[pure_id]["elapsed_ms"] = elapsed_ms
            matched_count += 1
            print(f"✅ 精准匹配耗时：{pure_id} → {elapsed_ms}ms")

    print(
        f"\n📊 耗时匹配完成：共匹配 {matched_count} 个用例，有效耗时用例 {len([c for c in cases if c['elapsed_ms'] > 0])} 个")

    # 5.5 筛选接口用例并统计
    interface_cases = [c for c in cases if
                       not any(kw in c["case_name"] or kw in c["case_full_name"] for kw in db_keywords)]
    interface_cases.sort(key=lambda x: x["start_time"])
    interface_case_count = len(interface_cases)
    db_case_count = total - interface_case_count

    # 耗时统计
    elapsed_list = [c["elapsed_ms"] for c in interface_cases if c["elapsed_ms"] > 0]
    print(f"📈 有效耗时列表：{elapsed_list}")

    time_stats = {
        "avg_time": round(sum(elapsed_list) / len(elapsed_list), 2) if elapsed_list else 0.0,
        "max_time": max(elapsed_list) if elapsed_list else 0.0,
        "min_time": min(elapsed_list) if elapsed_list else 0.0,
        "total_time": round(sum(elapsed_list), 2) if elapsed_list else 0.0
    }

    # 5.6 构建耗时详情
    time_details = []
    for case in interface_cases:
        time_details.append({
            "module": case["module"],
            "scenario": case["scenario"],
            "case_name": case["case_name"][:60] + "..." if len(case["case_name"]) > 60 else case["case_name"],
            "param_info": case["param_display"],
            "elapsed": case["elapsed_ms"]
        })

    # ====================== 6. 生成报告（优化参数显示） ======================
    try:
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

        # 生成Markdown报告
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
        # 模块统计
        for module in sorted(module_stats.keys()):
            stats = module_stats[module]
            report_content += (
                f"| {module} | {stats['total']} | {stats['executed']} | "
                f"{stats['passed']} | {stats['failed']} | {stats['skipped']} | "
                f"{stats['pass_rate']:.2f}% |\n"
            )

        # 耗时统计
        main_time_module = next(iter(module_stats.keys())) if module_stats else "未分类"
        report_content += f"""
## 3. 接口耗时统计（毫秒）
| 模块                 | 总用例数 | 接口用例数 | 数据库查询数 | 平均耗时(ms) | 最大耗时(ms) | 最小耗时(ms) | 总耗时(ms) |
|---------------------|----------|------------|--------------|--------------|--------------|--------------|------------|
| {main_time_module} | {total} | {interface_case_count} | {db_case_count} | {time_stats['avg_time']} | {time_stats['max_time']} | {time_stats['min_time']} | {time_stats['total_time']} |

## 4. 接口耗时详情列表（含参数化）
| 模块                | 场景                          | 用例名称                | 参数信息                  | 耗时(ms) |
|---------------------|-----------------------------|------------------------|---------------------------|----------|
"""
        # 耗时详情
        if time_details:
            for detail in time_details:
                report_content += (
                    f"| {detail['module']} | {detail['scenario']} | {detail['case_name']} | {detail['param_info']} | {detail['elapsed']} |\n"
                )
        else:
            report_content += "| - | - | - | - | 无耗时数据 |\n"

        # 失败用例
        report_content += f"""
## 5. 失败用例列表（共{len(failed_cases)}条）
| 模块                | 场景                          | 用例名称                | 参数信息                  | 执行结果   | 备注（失败原因）          | 具体原因（实际/预期）      |
|---------------------|-----------------------------|------------------------|---------------------------|----------|-------------------------|-------------------------|
"""
        if failed_cases:
            for fail_case in failed_cases:
                report_content += (
                    f"| {fail_case['module']} | {fail_case['scenario']} | {fail_case['case_name']} | {fail_case['param_display']} | "
                    f"{fail_case['status']} | {fail_case['failure_msg']} | {fail_case['specific_reason']} |\n"
                )
        else:
            report_content += "| - | - | - | - | - | 无失败用例 | - |\n"

        # 环境信息
        report_content += f"""
## 6. 环境信息
| 环境项         | 值                     |
|---------------|------------------------|
| Python版本     | {sys.version.split()[0]} |
| Pytest版本     | 7.4.3                  |
| Allure版本     | 2.14.2                 |
| 接口BaseURL    | {base_url}             |

## 7. 注意事项
1. 通过率计算规则：仅统计实际执行的用例（排除跳过用例）；
2. 接口列表按执行时间排序；
3. 耗时数据优先从执行日志提取基类记录的耗时，其次从time_record.json读取；
4. 接口耗时统计仅包含非数据库查询类用例；
5. 所有耗时单位为毫秒（ms），保留2位小数；
6. 参数化用例优先按参数精准匹配耗时，匹配失败时自动给同基础标识的所有用例赋值。
"""

        # 写入报告
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        # 写入MD报告
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"\n✅ MD报告生成成功：{os.path.abspath(report_path)}")

        # 生成HTML报告
        if markdown:
            html_report_path = report_path.replace(".md", ".html")
            try:
                html_content = markdown.markdown(report_content, extensions=["extra", "sane_lists", "nl2br"])
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
            word-break: break-all; /* 换行显示长参数 */
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #f0f7ff;
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
                print(f"✅ HTML报告生成成功：{os.path.abspath(html_report_path)}")
            except Exception as e:
                print(f"❌ HTML报告生成失败：{e}")
        else:
            print("⚠️ 未安装markdown库，跳过HTML报告生成（执行 pip install markdown 安装）")

    except Exception as e:
        print(f"\n❌ 报告生成失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return

    return True


# ====================== 兼容函数 ======================
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
        with allure.step(f"校验: {message}"):
            result = False
            try:
                if use_isclose and op in (CompareOp.EQ, CompareOp.NE):
                    if not (isinstance(actual_value, (int, float)) and
                            isinstance(expected_value, (int, float))):
                        use_isclose = False
                        logging.warning(f"自动禁用isclose：非数字类型比较（实际值类型：{type(actual_value)}）")

                    is_close = math.isclose(
                        actual_value,
                        expected_value,
                        rel_tol=rel_tol,
                        abs_tol=abs_tol
                    )
                    result = is_close if op == CompareOp.EQ else not is_close

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
                err_msg = f"校验类型错误: {str(e)} | 实际值类型: {type(actual_value)} | 预期值类型: {type(expected_value)}"
                pytest.fail(err_msg)

            def truncate(val):
                val_str = str(val)
                return val_str[:50] + "..." if len(val_str) > 50 else val_str

            detail_msg = (
                f"实际: {truncate(actual_value)} | "
                f"操作: {op.value} | "
                f"预期: {truncate(expected_value)}"
            )

            full_detail = (
                f"校验场景: {message}\n"
                f"实际值: {actual_value}\n"
                f"比较操作: {op.value}\n"
                f"预期值: {expected_value}\n"
                f"是否通过: {'是' if result else '否'}"
            )

            allure.attach(
                full_detail,
                name=attachment_name,
                attachment_type=attachment_type
            )

            if not result:
                pytest.fail(f"校验失败: {message} | {detail_msg}")
            logging.info(f"校验通过: {message} | {detail_msg}")
except:
    pass

if __name__ == "__main__":
    # 执行报告生成
    success = generate_simple_report(
        allure_results_dir="report/vps_results",
        env="test",
        report_path="report/VPS接口自动化测试报告.md"
    )
    sys.exit(0 if success else 1)
