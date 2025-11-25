import json
import sys
import os
import re
import math
from collections import Counter, defaultdict
import markdown
from datetime import datetime

# 兼容Python路径（根据项目结构调整）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目依赖（若缺少相关模块，需确保项目结构正确）
try:
    from lingkuanMT5_1120.config import ENV_CONFIG, Environment
    from VAR.VAR import PROJECT_NAME  # 确保VAR.py中定义了PROJECT_NAME
    from commons.api_base import *
except ImportError as e:
    print(f"导入项目依赖警告：{str(e)}，部分环境信息可能无法显示")
    PROJECT_NAME = "自研跟单"  # 兜底项目名称
    ENV_CONFIG = {}
    Environment = type('Environment', (), {})  # 兜底Environment类

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
    CompareOp = type('CompareOp', (), {})  # 兜底枚举类
    CompareOp.EQ = type('EQ', (), {'value': '等于'})
    CompareOp.NE = type('NE', (), {'value': '不等于'})
    CompareOp.GT = type('GT', (), {'value': '大于'})
    CompareOp.LT = type('LT', (), {'value': '小于'})
    CompareOp.GE = type('GE', (), {'value': '大于等于'})
    CompareOp.LE = type('LE', (), {'value': '小于等于'})
    CompareOp.IN = type('IN', (), {'value': '包含于'})
    CompareOp.NOT_IN = type('NOT_IN', (), {'value': '不包含于'})


def generate_simple_report(allure_results_dir, env, report_path, error_msg_prefix=""):
    """
    生成简化版MD+HTML测试报告（适配状态码断言失败、JSON断言、超时等场景）
    :param allure_results_dir: Allure结果目录路径（如report/vps_results）
    :param env: 执行环境（如test/prod）
    :param report_path: MD报告输出路径（如report/VPS接口自动化测试报告.md）
    :param error_msg_prefix: 错误信息前缀（可选）
    """
    # -------------------------- 1. 前置校验：确保输入有效 --------------------------
    if not os.path.exists(allure_results_dir):
        print(f"错误：Allure结果目录不存在！路径：{allure_results_dir}")
        return

    result_files = []
    for root, dirs, files in os.walk(allure_results_dir):
        for file in files:
            if file.endswith(".json") and "result" in file:
                result_files.append(os.path.join(root, file))
    if not result_files:
        print(f"警告：Allure结果目录 {allure_results_dir} 下无测试结果文件（*result.json）")
    else:
        print(f"找到 {len(result_files)} 个测试结果文件，开始生成报告...")

    # -------------------------- 2. 收集用例结果 --------------------------
    all_case_results = []
    start_time_ts = None
    end_time_ts = None

    for root, dirs, files in os.walk(allure_results_dir):
        for file in files:
            if file.endswith(".json") and "result" in file:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"警告：JSON解析失败 {file_path}，错误：{str(e)}，跳过该文件")
                    continue
                except PermissionError as e:
                    print(f"警告：权限不足，无法读取 {file_path}，错误：{str(e)}，跳过该文件")
                    continue
                except Exception as e:
                    print(f"警告：读取文件失败 {file_path}，错误：{str(e)}，跳过该文件")
                    continue

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

                # 状态映射
                status = data.get("status", "unknown").upper()
                final_status = "FAILED" if status == "BROKEN" else status
                if final_status not in ["PASSED", "FAILED", "SKIPPED"]:
                    final_status = "FAILED"

                # 提取模块和场景
                module = "未分类"
                scenario = "-"
                labels = data.get("labels", [])
                for label in labels:
                    if label.get("name") == "feature":
                        module = label.get("value", "未分类")
                    elif label.get("name") == "story":
                        scenario_val = label.get("value", "").strip()
                        scenario = scenario_val if scenario_val else "-"

                # 初始化失败信息
                status_details = data.get("statusDetails", {})
                failure_msg = "-"
                specific_reason = "-"

                # 失败场景提取
                if final_status == "FAILED":
                    msg = status_details.get("message", "").strip()
                    trace = status_details.get("trace", "").strip()

                    # 场景1：数据库超时
                    if "TimeoutError" in trace and ("等待" in msg or "删除" in msg or "超时" in msg or "查询" in msg):
                        failure_msg = msg[:80]
                        specific_reason = ""

                    # 场景2：JSON断言失败
                    elif "AssertionError" in trace and ("JSON路径" in msg or "响应" in msg):
                        json_match = re.search(r'Failed: ([^（]+)', msg)
                        failure_msg = json_match.group(1).strip()[:80] if json_match else "响应字段断言失败"
                        actual_expected_match = re.search(r'预期: (.*?), 实际: (.*?)(?:）|$)', msg)
                        if actual_expected_match:
                            expected_val = actual_expected_match.group(1).strip()
                            actual_val = actual_expected_match.group(2).strip()
                            specific_reason = f"实际: {actual_val}，预期: {expected_val}"
                        else:
                            specific_reason = "未获取到实际/预期信息"

                    # 场景3：手数列表不匹配
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

                    # 场景4：状态码断言失败（仅保留预期和实际状态码）
                    elif "AssertionError" in trace and "状态码不匹配" in msg:
                        # 提取业务原因
                        failure_match = re.search(r'Failed: ([^（]+)', msg)
                        failure_msg = f"{failure_match.group(1).strip()}（状态码不匹配）" if failure_match else "状态码断言失败"
                        # 提取预期/实际状态码
                        expected_match = re.search(r'预期: (\d+)', msg)
                        actual_match = re.search(r'实际: (\d+)', msg)
                        expected_val = expected_match.group(1) if expected_match else "未知"
                        actual_val = actual_match.group(1) if actual_match else "未知"
                        # 拼接具体原因（仅保留预期和实际状态码）
                        specific_reason = (
                            f"预期状态码: {expected_val}<br>"
                            f"实际状态码: {actual_val}"
                        )

                    # 场景5：其他失败
                    else:
                        failure_match = re.search(r'校验失败: ([^|]+) \| 实际:', msg)
                        failure_msg = failure_match.group(1).strip()[:80] if failure_match else msg[:80] or "无详细原因"
                        actual_match = re.search(r'实际: ([^|]+)', msg)
                        expected_match = re.search(r'预期: ([^|]+)', msg)
                        if actual_match and expected_match:
                            specific_reason = f"实际: {actual_match.group(1).strip()}，预期: {expected_match.group(1).strip()}"
                        else:
                            specific_reason = "未获取到实际/预期信息"

                # 添加用例结果
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

    # -------------------------- 3. 用例去重 --------------------------
    case_groups = defaultdict(list)
    for case in all_case_results:
        case_groups[case["case_unique_id"]].append(case)
    case_final_results = {}
    for case_id, cases in case_groups.items():
        cases_sorted = sorted(cases, key=lambda x: x["stop_time"], reverse=True)
        case_final_results[case_id] = cases_sorted[0]
    final_cases = list(case_final_results.values())

    # -------------------------- 4. 统计计算 --------------------------
    total = len(final_cases)
    passed = sum(1 for case in final_cases if case["status"] == "PASSED")
    failed = sum(1 for case in final_cases if case["status"] == "FAILED")
    skipped = sum(1 for case in final_cases if case["status"] == "SKIPPED")
    executed_total = total - skipped
    global_pass_rate = round((passed / executed_total) * 100, 2) if executed_total > 0 else 0.0

    # 时间转换（修复命名冲突）
    import datetime  # 再次导入，确保无覆盖
    def timestamp_to_str(ts):
        if not ts or ts == 0:
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ts_seconds = int(ts // 1000)
        try:
            return datetime.datetime.fromtimestamp(ts_seconds).strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print(f"时间戳转换失败（原始ts: {ts}，转换后秒级: {ts_seconds}），错误：{str(e)}")
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    start_time = timestamp_to_str(start_time_ts)
    end_time = timestamp_to_str(end_time_ts)

    # 总耗时计算
    if start_time_ts and end_time_ts:
        total_seconds = int((end_time_ts - start_time_ts) // 1000)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        duration = f"{hours}时{minutes:02d}分{seconds:02d}秒" if hours > 0 else f"{minutes}分{seconds:02d}秒"
    else:
        duration = "未知"

    # 模块统计
    module_stats = defaultdict(
        lambda: {"total": 0, "executed": 0, "passed": 0, "failed": 0, "skipped": 0, "pass_rate": 0.0}
    )
    for case in final_cases:
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
                (module_stats[module]["passed"] / module_stats[module]["executed"]) * 100, 2
            )

    # 失败用例排序
    failed_cases = [case for case in final_cases if case["status"] == "FAILED"]
    failed_cases.sort(key=lambda x: (x["module"], x["scenario"], x["case_name"]))

    # -------------------------- 5. 项目名称和报告标题 --------------------------
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

    # -------------------------- 6. 环境信息 --------------------------
    try:
        base_url = ENV_CONFIG[Environment[env.upper()]]['base_url']
    except (KeyError, ValueError, AttributeError):
        base_url = "未知环境URL"

    # -------------------------- 7. 生成MD报告内容 --------------------------
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

    report_content += f"""
## 3. 失败用例列表（共{len(failed_cases)}条）
| 模块                | 场景                          | 用例名称                | 执行结果   | 备注（失败原因）          | 具体原因（实际/预期）      |
|---------------------|-----------------------------|------------------------|----------|-------------------------|-------------------------|
"""
    if failed_cases:
        for fail_case in failed_cases:
            case_name = fail_case["case_name"]
            if len(case_name) > 60:
                case_name = case_name[:60] + "..."
            report_content += (
                f"| {fail_case['module']} | {fail_case['scenario']} | {case_name} | "
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
2. 失败用例优先查看"备注"和"具体原因"，详细操作步骤请参考Allure HTML报告；
"""

    # -------------------------- 8. 写入MD报告 --------------------------
    try:
        report_dir = os.path.dirname(report_path)
        os.makedirs(report_dir, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"MD报告生成成功！路径：{os.path.abspath(report_path)}")
    except Exception as e:
        print(f"写入MD报告失败！错误：{str(e)}")
        print(f"请检查报告路径是否可写：{report_path}")
        return

    # -------------------------- 9. 生成HTML报告 --------------------------
    html_report_path = report_path.replace(".md", ".html")
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        html_content = markdown.markdown(
            md_content,
            extensions=[
                "extra",
                "sane_lists",
                "nl2br"
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
            line-height: 1.8;
            padding: 20px;
            max-width: 1600px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 28px;
            color: #2c3e50;
            text-align: center;
            margin: 30px 0;
            padding-bottom: 15px;
            border-bottom: 2px solid #3498db;
        }}
        h2 {{
            font-size: 22px;
            color: #2c3e50;
            margin: 40px 0 20px;
            padding-left: 10px;
            border-left: 4px solid #3498db;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        th {{
            background-color: #3498db;
            color: white;
            padding: 12px 15px;
            text-align: left;
            font-weight: bold;
            border: 1px solid #2980b9;
        }}
        td {{
            padding: 12px 15px;
            border: 1px solid #ddd;
            text-align: left;
            word-break: break-all;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        tr:hover {{
            background-color: #e8f4fd;
        }}
        .notes {{
            margin: 20px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #bdc3c7;
            border-radius: 4px;
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
        print(f"HTML报告生成成功！路径：{os.path.abspath(html_report_path)}")
    except ImportError as e:
        print(f"MD转HTML失败：缺少依赖包！错误：{str(e)}")
        print("请执行命令安装：pip install markdown")
    except Exception as e:
        print(f"MD转HTML失败！错误：{str(e)}")

    # -------------------------- 10. 输出统计信息 --------------------------
    print(f"\n报告统计汇总：")
    print(f"- 总用例数：{total}")
    print(f"- 通过数：{passed}")
    print(f"- 失败数：{failed}")
    print(f"- 跳过数：{skipped}")
    print(f"- 整体通过率：{global_pass_rate:.2f}%")
    print(f"- 涉及模块数：{len(module_stats)}个")


# 兼容verify_data函数（避免导入报错）
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
        """通用数据校验函数（支持浮点容错比较）"""
        with allure.step(f"校验: {message}"):
            result = False
            try:
                # 浮点容错比较（仅对EQ/NE生效）
                if use_isclose and op in (CompareOp.EQ, CompareOp.NE):
                    if not (isinstance(actual_value, (int, float)) and isinstance(expected_value, (int, float))):
                        use_isclose = False
                        logging.warning(f"自动禁用isclose：非数字类型比较（实际值类型：{type(actual_value)}）")
                    else:
                        is_close = math.isclose(actual_value, expected_value, rel_tol=rel_tol, abs_tol=abs_tol)
                        result = is_close if op == CompareOp.EQ else not is_close

                # 普通比较逻辑
                if not use_isclose:
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

            # 生成详细提示信息
            def truncate(val):
                val_str = str(val)
                return val_str[:50] + "..." if len(val_str) > 50 else val_str

            detail_msg = (
                f"实际: {truncate(actual_value)} | "
                f"操作: {op.value} | "
                f"预期: {truncate(expected_value)}"
            )

            # 写入Allure附件
            full_detail = (
                f"校验场景: {message}\n"
                f"实际值: {actual_value}\n"
                f"比较操作: {op.value}\n"
                f"预期值: {expected_value}\n"
                f"是否通过: {'是' if result else '否'}"
            )
            allure.attach(full_detail, name=attachment_name, attachment_type=attachment_type)

            if not result:
                pytest.fail(f"校验失败: {message} | {detail_msg}")
            logging.info(f"校验通过: {message} | {detail_msg}")
except:
    pass

# 测试入口（直接运行脚本时执行）
if __name__ == "__main__":
    # 示例：生成VPS环境报告
    generate_simple_report(
        allure_results_dir="report/vps_results",
        env="test",
        report_path="report/VPS接口自动化测试报告.md"
    )
