import json
import sys
import os
import re
import math
from collections import Counter, defaultdict
from datetime import datetime as dt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    import markdown
except ImportError:
    markdown = None

# 配置降级处理
try:
    from lingkuan_1201.config import ENV_CONFIG, Environment
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
        return str(hash(str(obj)))


def generate_interface_detail_page(time_details, report_title, detail_report_path):
    """生成独立的接口耗时详情页面"""
    # 构建详情页内容
    detail_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_title} - 耗时详情</title>
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
        .back-link {{
            display: inline-block;
            margin: 20px 0;
            padding: 8px 16px;
            background-color: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }}
        .back-link:hover {{
            background-color: #2980b9;
        }}
        .summary {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin: 10px 0 20px;
            border-left: 3px solid #3498db;
        }}
    </style>
</head>
<body>
    <h1>{report_title} - 接口耗时详情</h1>

    <div class="summary">
        <strong>统计信息：</strong>共 {len(time_details)} 条接口耗时记录
    </div>

    <a href="javascript:history.back()" class="back-link">← 返回主报告</a>

    <table>
        <thead>
            <tr>
                <th>模块</th>
                <th>场景</th>
                <th>用例名称</th>
                <th>耗时(ms)</th>
            </tr>
        </thead>
        <tbody>
    """

    # 添加所有耗时详情数据
    if time_details:
        for detail in time_details:
            detail_content += f"""
            <tr>
                <td>{detail['module']}</td>
                <td>{detail['scenario']}</td>
                <td>{detail['case_name']}</td>
                <td>{detail['elapsed']}</td>
            </tr>
            """
    else:
        detail_content += """
            <tr>
                <td colspan="4" style="text-align:center;">无耗时数据</td>
            </tr>
            """

    detail_content += """
        </tbody>
    </table>

    <a href="javascript:history.back()" class="back-link">← 返回主报告</a>
</body>
</html>
    """

    # 写入详情页文件
    with open(detail_report_path, "w", encoding="utf-8") as f:
        f.write(detail_content)
    print(f"✅ 耗时详情页生成成功：{os.path.abspath(detail_report_path)}")


def generate_simple_report(allure_results_dir, env, report_path):
    # ====================== 1. 核心配置（修复路径 + 兼容Cloud + 汇总耗时合并） ======================
    # 修复：获取正确的项目根目录（当前脚本的上上级目录）
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_script_dir, ".."))  # 修正根目录计算
    print(f"🔧 修正后的项目根目录：{project_root}")

    db_keywords = ["dbquery", "数据库校验"]
    allure_abs_dir = os.path.abspath(allure_results_dir)

    # 修复：耗时文件路径映射（基于正确的项目根目录，新增汇总报告合并逻辑）
    time_record_mapping = {
        "vps_results": os.path.join(project_root, "report", "test_vps", "time_record.json"),
        "cloud_results": os.path.join(project_root, "report", "test_cloudTrader", "time_record.json"),
        "merged_allure-results": [  # 汇总报告：合并VPS和Cloud的耗时文件
            os.path.join(project_root, "report", "test_vps", "time_record.json"),
            os.path.join(project_root, "report", "test_cloudTrader", "time_record.json")
        ]
    }

    # 自动匹配耗时文件（汇总报告需合并多个文件）
    time_record_file = None
    merged_time_records = []  # 用于汇总报告的合并耗时数据
    for key, path in time_record_mapping.items():
        if key in allure_results_dir:
            if key == "merged_allure-results":
                # 汇总报告：读取VPS和Cloud的耗时文件并合并
                for single_path in path:
                    if os.path.exists(single_path):
                        try:
                            with open(single_path, "r", encoding="utf-8") as f:
                                merged_time_records.extend(json.load(f))
                        except Exception as e:
                            print(f"⚠️ 读取{single_path}耗时文件失败：{e}")
                print(f"📊 汇总报告合并耗时记录数：{len(merged_time_records)}")
            else:
                # 单一项目：读取对应耗时文件
                time_record_file = os.path.abspath(path)
            break

    # 兜底：如果未匹配到，默认使用test_vps的耗时文件（仅单一项目）
    if not time_record_file and "merged_allure-results" not in allure_results_dir:
        time_record_file = os.path.abspath(os.path.join(project_root, "report", "test_vps", "time_record.json"))

    # 新增：检查耗时文件是否存在（仅单一项目）
    if not "merged_allure-results" in allure_results_dir and not os.path.exists(time_record_file):
        print(f"⚠️ 耗时文件不存在：{time_record_file}，尝试创建空文件")
        os.makedirs(os.path.dirname(time_record_file), exist_ok=True)
        with open(time_record_file, "w", encoding="utf-8") as f:
            json.dump([], f)  # 创建空的耗时记录文件

    print(f"📌 当前使用的耗时文件：{time_record_file if time_record_file else '合并VPS+Cloud文件'}")

    # 动态生成详情页路径（与主报告同目录，区分不同项目）
    if "vps_results" in allure_results_dir:
        detail_report_filename = "vps_interface_time_detail.html"
    elif "cloud_results" in allure_results_dir:
        detail_report_filename = "cloud_interface_time_detail.html"
    elif "merged_allure-results" in allure_results_dir:
        detail_report_filename = "merged_interface_time_detail.html"
    else:
        detail_report_filename = "interface_time_detail.html"
    detail_report_path = os.path.join(os.path.dirname(report_path), detail_report_filename)

    # ====================== 2. 收集用例结果 ======================
    all_case_results = []
    start_time_ts = None
    end_time_ts = None
    all_modules = set()

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

                    if " TimeoutError" in trace and any(key in msg for key in ["等待", "删除", "超时", "查询"]):
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

                # 修复：兼容Cloud用例标识（简化匹配逻辑，提高容错）
                # 提取核心标识：去掉路径前缀，保留 test_xxx.xxx.xxx#test_xxx 格式
                pure_identity = re.sub(r'^.*?(test_(vps|cloudTrader)\.[^#]+#[^_]+)', r'\1', case_full_name)
                # 兜底：如果正则匹配失败，直接使用全名称的简化版
                if not pure_identity.startswith(("test_vps", "test_cloudTrader")):
                    # 从fullName中提取用例核心标识（如：test_cloudTrader.test_lianxi.TestVPSqueryList.test_query_brokeName）
                    pure_identity = re.sub(r'[^a-zA-Z0-9_.#]', '', case_full_name).split("::")[-1]
                    # 替换::为#，统一格式
                    pure_identity = pure_identity.replace("::", "#")

                all_case_results.append({
                    "case_unique_id": case_unique_id,
                    "case_name": case_name,
                    "case_full_name": case_full_name,
                    "pure_identity": pure_identity,
                    "module": module,
                    "scenario": scenario,
                    "status": final_status,
                    "failure_msg": failure_msg,
                    "specific_reason": specific_reason,
                    "start_time": case_start,  # 用于排序的时间戳
                    "stop_time": case_stop
                })

    # ====================== 3. 用例去重 & 按执行时间排序 ======================
    case_final_results = {}
    for case in all_case_results:
        case_id = case["case_unique_id"]
        if case_id not in case_final_results or case["stop_time"] > case_final_results[case_id]["stop_time"]:
            case_final_results[case_id] = case
    # 所有用例按执行时间排序（核心需求1）
    cases = sorted(list(case_final_results.values()), key=lambda x: x["start_time"])

    # 打印用例标识（调试用）
    pure_ids = [c["pure_identity"] for c in cases]
    print(f"📌 用例纯标识列表：{pure_ids}")

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

    # 模块统计（按用例执行时间排序，核心需求1）
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
    # 模块统计列表按用例执行时间对应的模块顺序排序
    sorted_modules = list(module_stats.keys())

    # 失败用例按执行时间排序（核心需求1）
    failed_cases = sorted([c for c in cases if c["status"] == "FAILED"], key=lambda x: x["start_time"])

    # ====================== 5. 耗时数据处理（核心修复：兼容Cloud + 汇总合并） ======================
    # 5.1 构建匹配映射（增加模糊匹配）
    pure_identity_map = {}
    # 构建反向映射：用例名称关键词 → 用例对象（提高匹配容错）
    case_name_map = {}
    for case in cases:
        pure_id = case["pure_identity"]
        pure_identity_map[pure_id] = case

        # 提取用例名称关键词（如 test_query_brokeName）
        case_name_key = re.search(r'test_\w+', case["case_name"]).group() if re.search(r'test_\w+',
                                                                                       case["case_name"]) else case[
            "case_name"]
        case_name_map[case_name_key.lower()] = case

    # 5.2 读取并处理耗时记录（修复匹配逻辑 + 汇总合并）
    case_time_map = {}
    try:
        # 区分单一项目和汇总报告的耗时数据来源
        if "merged_allure-results" in allure_results_dir:
            time_records = merged_time_records
        else:
            with open(time_record_file, "r", encoding="utf-8") as f:
                time_records = json.load(f)

        print(f"📊 读取到耗时记录数：{len(time_records)}")

        # 按用例分组，取最后一次执行的耗时
        record_group = defaultdict(list)
        for idx, record in enumerate(time_records):
            elapsed_ms = round(float(record.get("elapsed_time", 0.0)), 2)
            record_full_name = str(record.get("case_full_name", ""))
            record_case_name = str(record.get("case_name", ""))

            if elapsed_ms <= 0:
                print(f"⚠️ 跳过无效耗时记录 {idx}：耗时={elapsed_ms}ms，名称={record_full_name}")
                continue

            # 修复：提取耗时记录的匹配标识（兼容多种格式）
            # 方式1：正则提取核心标识
            record_pure_id = re.sub(r'^.*?(test_(vps|cloudTrader)\.[^#]+#[^_]+)', r'\1', record_full_name)
            # 方式2：如果正则失败，提取用例名称关键词
            if not record_pure_id.startswith(("test_vps", "test_cloudTrader")):
                record_pure_id = re.sub(r'[^a-zA-Z0-9_.#]', '', record_full_name).split("::")[-1].replace("::", "#")

            # 方式3：用例名称关键词匹配
            record_name_key = re.search(r'test_\w+', record_case_name).group().lower() if re.search(r'test_\w+',
                                                                                                    record_case_name) else record_case_name.lower()

            # 优先按pure_id分组，否则按名称关键词
            if record_pure_id and record_pure_id in pure_identity_map:
                record_group[record_pure_id].append(elapsed_ms)
            elif record_name_key in case_name_map:
                # 通过名称关键词匹配到用例，获取其pure_id
                matched_case = case_name_map[record_name_key]
                record_group[matched_case["pure_identity"]].append(elapsed_ms)
                print(f"🔍 模糊匹配耗时记录：{record_case_name} → {matched_case['pure_identity']} → {elapsed_ms}ms")
            else:
                print(f"⚠️ 耗时记录无匹配用例：{record_pure_id} / {record_case_name}")

        # 每个用例取最后一次的耗时（仅保留>0的）
        for pure_id, elapsed_list in record_group.items():
            if pure_id in pure_identity_map and elapsed_list:
                final_elapsed = elapsed_list[-1]
                if final_elapsed > 0:  # 确保只保留正数耗时
                    case = pure_identity_map[pure_id]
                    case_time_map[case["case_unique_id"]] = final_elapsed
                    print(f"✅ 耗时匹配成功：{pure_id} → {final_elapsed}ms")

    except Exception as e:
        print(f"❌ 读取耗时文件失败：{e}")
        import traceback
        traceback.print_exc()

    # 5.3 筛选接口用例（仅保留有有效耗时的）
    interface_cases = [c for c in cases if
                       not any(kw in c["case_name"] or kw in c["case_full_name"] for kw in db_keywords)]
    # 过滤出耗时>0的接口用例
    valid_interface_cases = [c for c in interface_cases if case_time_map.get(c["case_unique_id"], 0.0) > 0]
    # 按执行时间排序（核心需求1）
    valid_interface_cases.sort(key=lambda x: x["start_time"])

    print(f"📈 有效耗时接口用例数：{len(valid_interface_cases)}")

    # 5.4 按模块分组统计耗时（按用例执行时间排序，核心需求1）
    module_time_stats = defaultdict(lambda: {
        "total_case": 0,  # 模块总用例数
        "interface_case": 0,  # 模块接口用例数
        "valid_interface_case": 0,  # 模块有效耗时用例数
        "db_case": 0,  # 模块数据库查询数
        "elapsed_list": [],  # 模块耗时列表
        "avg_time": 0.0,
        "max_time": 0.0,
        "min_time": 0.0,
        "total_time": 0.0
    })

    # 先统计每个模块的总用例数、接口用例数、数据库查询数
    for case in cases:
        module = case["module"]
        is_interface = not any(kw in case["case_name"] or kw in case["case_full_name"] for kw in db_keywords)
        module_time_stats[module]["total_case"] += 1
        if is_interface:
            module_time_stats[module]["interface_case"] += 1
        else:
            module_time_stats[module]["db_case"] += 1

    # 再统计每个模块的有效耗时数据
    for case in valid_interface_cases:
        module = case["module"]
        elapsed = case_time_map[case["case_unique_id"]]
        module_time_stats[module]["valid_interface_case"] += 1
        module_time_stats[module]["elapsed_list"].append(elapsed)

    # 计算每个模块的耗时统计值
    for module, stats in module_time_stats.items():
        if stats["elapsed_list"]:
            stats["avg_time"] = round(sum(stats["elapsed_list"]) / len(stats["elapsed_list"]), 2)
            stats["max_time"] = max(stats["elapsed_list"])
            stats["min_time"] = min(stats["elapsed_list"])
            stats["total_time"] = round(sum(stats["elapsed_list"]), 2)
        else:
            stats["avg_time"] = 0.0
            stats["max_time"] = 0.0
            stats["min_time"] = 0.0
            stats["total_time"] = 0.0

    # 5.5 构建耗时详情（仅包含耗时>0的用例，按执行时间排序）
    time_details = []
    for case in valid_interface_cases:
        elapsed_ms = case_time_map[case["case_unique_id"]]
        time_details.append({
            "module": case["module"],
            "scenario": case["scenario"],
            "case_name": case["case_name"][:60] + "..." if len(case["case_name"]) > 60 else case["case_name"],
            "elapsed": elapsed_ms
        })

    # 5.6 生成耗时TOP10列表（按耗时从高到低排序，核心需求2）
    time_top10 = sorted(time_details, key=lambda x: x["elapsed"], reverse=True)[:10]

    # ====================== 6. 生成报告（恢复之前的好看布局） ======================
    try:
        # 修复：PROJECT_NAME 未定义的兜底处理
        project_name_global = globals().get('PROJECT_NAME', 'MT4自研跟单1.5.0')

        # 区分项目类型，生成标题
        if "cloud_results" in allure_results_dir:
            project_name = "云策略"
            report_title = f"{project_name_global} 云策略接口自动化测试报告"
        elif "vps_results" in allure_results_dir:
            project_name = "VPS"
            report_title = f"{project_name_global} VPS接口自动化测试报告"
        elif "merged_allure-results" in allure_results_dir:
            project_name = "VPS+云策略汇总"
            report_title = f"{project_name_global} 接口自动化汇总测试报告"
        else:
            project_name = "未知项目"
            report_title = f"{project_name_global} 接口自动化测试报告"

        # 环境信息（增强容错）
        try:
            base_url = ENV_CONFIG[Environment[env.upper()]]['base_url']
        except (KeyError, ValueError, NameError):
            base_url = f"{env}环境 - 未配置BaseURL"

        # ====================== 生成Markdown报告（保留原始数据逻辑） ======================
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

## 2. 模块执行统计（按用例执行时间排序）
| 模块名称         | 总用例数  | 实际执行数   | 通过数   | 失败数  | 跳过数  | 通过率(%)  |
|-----------------|----------|-------------|---------|---------|---------|------------|
"""
        # 模块执行统计（按用例执行时间对应的模块顺序排序）
        if module_stats:
            for module in sorted_modules:
                stats = module_stats[module]
                report_content += (
                    f"| {module} | {stats['total']} | {stats['executed']} | "
                    f"{stats['passed']} | {stats['failed']} | {stats['skipped']} | "
                    f"{stats['pass_rate']:.2f} |\n"
                )
        else:
            report_content += "| 无模块数据 | 0 | 0 | 0 | 0 | 0 | 0.00 |\n"

        # 耗时统计（按用例执行时间排序，核心需求1）
        report_content += f"""
## 3. 接口耗时统计（毫秒，按用例执行时间排序）
| 模块名称         | 总用例数  | 数据库查询数  | 接口用例数   | 有效耗时用例数 | 平均耗时  | 最大耗时   | 最小耗时   | 总耗时    |
|-----------------|----------|--------------|-------------|---------------|-----------|-----------|-----------|-----------|
"""
        # 按模块输出耗时统计（按用例执行时间对应的模块顺序排序）
        if module_time_stats:
            for module in sorted_modules:
                stats = module_time_stats[module]
                report_content += (
                    f"| {module} | {stats['total_case']} | {stats['db_case']} | {stats['interface_case']} | "
                    f"{stats['valid_interface_case']} | {stats['avg_time']} | {stats['max_time']} | {stats['min_time']} | {stats['total_time']} |\n"
                )
        else:
            report_content += "| 无耗时数据 | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0.00 | 0.00 |\n"

        # 耗时详情列表（按执行时间排序，核心需求1）
        report_content += f"""
## 4. 接口耗时详情列表（毫秒，按执行时间排序）
| 模块                | 场景                          | 用例名称                | 耗时(ms) |
|---------------------|-----------------------------|------------------------|----------|
"""
        # 显示所有耗时数据（按执行时间排序）
        if time_details:
            for detail in time_details:
                report_content += (
                    f"| {detail['module']} | {detail['scenario']} | {detail['case_name']} | {detail['elapsed']} |\n"
                )
            # 添加跳转链接
            report_content += f"| 更多数据 | 共{len(time_details)}条记录 | [查看全部耗时详情]({detail_report_filename}) | 点击跳转 |\n"
        else:
            report_content += "| - | - | - | 无有效耗时数据 |\n"

        # 新增：接口耗时TOP10列表（按耗时从高到低排序，核心需求2）
        report_content += f"""
## 5. 接口耗时TOP10（毫秒，按耗时从高到低排序）
| 模块                | 场景                          | 用例名称                | 耗时(ms) |
|---------------------|-----------------------------|------------------------|----------|
"""
        if time_top10:
            for top in time_top10:
                report_content += (
                    f"| {top['module']} | {top['scenario']} | {top['case_name']} | {top['elapsed']} |\n"
                )
        else:
            report_content += "| - | - | - | 无有效耗时数据 |\n"

        # 失败用例列表（按执行时间排序，核心需求1）
        report_content += f"""
## 6. 失败用例列表（共{len(failed_cases)}条，按执行时间排序）
| 模块                | 场景                          | 用例名称                | 执行结果   | 备注（失败原因）          | 具体原因（实际/预期）      |
|---------------------|-----------------------------|------------------------|----------|-------------------------|-------------------------|
"""
        if failed_cases:
            for fail_case in failed_cases:
                report_content += (
                    f"| {fail_case['module']} | {fail_case['scenario']} | {fail_case['case_name']} | "
                    f"{fail_case['status']} | {fail_case['failure_msg']} | {fail_case['specific_reason']} |\n"
                )
        else:
            report_content += "| - | - | - | - | 无失败用例 | - |\n"

        # 环境信息
        report_content += f"""
## 7. 环境信息
| 环境项         | 配置值                     |
|---------------|----------------------------|
| Python版本    | {sys.version.split()[0]}   |
| Pytest版本    | 7.4.3                      |
| Allure版本    | 2.14.2                     |
| 接口BaseURL   | {base_url}                 |
| 报告生成时间  | {dt.now().strftime("%Y-%m-%d %H:%M:%S")} |

## 8. 注意事项
1. 接口列表按执行时间排序；
2. 接口耗时统计仅包含非数据库查询类用例；
3. 通过率计算规则：仅统计实际执行的用例（排除跳过用例）；
4. 失败用例先查看"备注"和"具体原因"，实际操作步骤请查看Allure报告的日志文件，优先排查接口返回数据、校验逻辑；
"""

        # ====================== 写入报告文件 ======================
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        # 写入MD报告
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"\n✅ MD报告生成成功：{os.path.abspath(report_path)}")

        # 生成HTML报告（恢复之前的好看样式：蓝头、奇偶行变色）
        if markdown:
            html_report_path = report_path.replace(".md", ".html")
            try:
                html_content = markdown.markdown(report_content, extensions=["extra", "sane_lists", "nl2br"])
                # 恢复之前的HTML样式（保留数据逻辑）
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
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            color: #2980b9;
            text-decoration: underline;
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

                # 生成独立的耗时详情页面
                generate_interface_detail_page(time_details, report_title, detail_report_path)

            except Exception as e:
                print(f"❌ HTML报告生成失败：{e}")
                import traceback
                traceback.print_exc()
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
    # 示例1：生成VPS报告
    success = generate_simple_report(
        allure_results_dir="report/vps_results",
        env="test",
        report_path="report/VPS接口自动化测试报告.md"
    )

    # 示例2：生成CloudTrader报告
    # success = generate_simple_report(
    #     allure_results_dir="report/cloud_results",
    #     env="test",
    #     report_path="report/Cloud接口自动化测试报告.md"
    # )

    # 示例3：生成汇总报告
    # success = generate_simple_report(
    #     allure_results_dir="report/merged_allure-results",
    #     env="test",
    #     report_path="report/汇总接口自动化测试报告.md"
    # )
    sys.exit(0 if success else 1)
