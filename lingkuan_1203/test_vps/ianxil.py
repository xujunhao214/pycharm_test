import json

# 替换为你实际的文件路径
file_path = "../report/vps_results/time_record.json"
with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)
    # 打印所有记录的用例方法和耗时
    for item in data:
        print(f"用例方法：{item['case_method']}，耗时：{item['elapsed_time']}ms")