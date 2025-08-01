#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 修复订单数据处理问题
import json
from datetime import datetime
import ast

from db_connector import *
import config


def query_mysql(query, params=None):
    """执行MySQL查询并返回结果"""
    conn = None
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"MySQL错误: {err}")
        print(f"问题查询: {query}")
        print(f"使用参数: {params}")
        return []
    finally:
        if conn:
            conn.close()


def query_redis(key):
    """查询Redis哈希表数据"""
    try:
        redis_conn = get_redis_connection()
        data = redis_conn.hgetall(key)
        if data:
            return {k.decode('utf-8'): v.decode('utf-8') for k, v in data.items()}
        return {}
    except Exception as e:
        print(f"Redis查询出错: {e}")
        return {}


def extract_order_info(order_value):
    """
    增强版订单信息提取
    专门处理格式: ['net.maku.followcom.pojo.EaOrderInfo', {订单字典}]
    """
    # 1. 尝试直接解析为Python对象
    try:
        if isinstance(order_value, str):
            parsed = ast.literal_eval(order_value)
            if isinstance(parsed, list) and len(parsed) == 2 and isinstance(parsed[1], dict):
                return parsed[1]
    except:
        pass

    # 2. 处理已经解析的列表格式
    if isinstance(order_value, list) and len(order_value) == 2:
        if isinstance(order_value[1], dict):
            return order_value[1]
        elif isinstance(order_value[1], str):
            try:
                return json.loads(order_value[1])
            except:
                pass

    # 3. 处理字典格式
    if isinstance(order_value, dict):
        return order_value

    # 4. 尝试JSON解析
    if isinstance(order_value, str):
        try:
            parsed = json.loads(order_value)
            if isinstance(parsed, list) and len(parsed) == 2 and isinstance(parsed[1], dict):
                return parsed[1]
            elif isinstance(parsed, dict):
                return parsed
        except:
            pass

    # 5. 尝试作为字符串直接处理
    if isinstance(order_value, str) and order_value.startswith("['net.maku."):
        try:
            # 手动提取字典部分
            dict_start = order_value.find('{')
            dict_end = order_value.rfind('}') + 1
            if dict_start != -1 and dict_end != -1:
                dict_str = order_value[dict_start:dict_end]
                return json.loads(dict_str)
        except:
            pass

    return None


def count_daily_lack_orders():
    """统计当日漏单数量"""
    today = datetime.today().strftime('%Y-%m-%d')
    total_lack_count = 0

    print(f"开始统计 {today} 的漏单数据...")

    for user in config.USER_CONFIG:
        print(f"\n处理用户配置: traderId={user['traderId']}, host={user['host']}")

        # 查询主交易员平台和账户
        master_info = query_mysql(
            "SELECT platform, account FROM follow_trader WHERE id = %s",
            (user['traderId'],)
        )

        if not master_info:
            print("  × 未找到主交易员信息")
            continue

        master_platform = master_info[0]['platform']
        master_account = master_info[0]['account']
        print(f"  √ 主交易员: {master_account} (平台: {master_platform})")

        # 查询订阅者ID
        follow_ids = query_mysql(
            "SELECT slave_id FROM follow_trader_subscribe WHERE master_id = %s",
            (user['traderId'],)
        )
        print(f"  找到 {len(follow_ids)} 个订阅者")

        for follow in follow_ids:
            follow_id = follow['slave_id']
            # 查询订阅者平台和账户
            follow_info = query_mysql(
                "SELECT platform, account FROM follow_trader WHERE id = %s",
                (follow_id,)
            )

            if not follow_info:
                print(f"    × 未找到订阅者ID: {follow_id}")
                continue

            follow_platform = follow_info[0]['platform']
            follow_account = follow_info[0]['account']
            print(f"    √ 处理订阅者: {follow_account} (平台: {follow_platform})")

            # 处理两种漏单状态
            for state in ['send', 'close']:
                # 构建Redis键
                redis_key = f"follow:repair:{state}:{user['host']}#{follow_platform}#{master_platform}#{follow_account}#{master_account}"
                print(f"      检查状态: {state}, Redis键: {redis_key}")

                # 获取Redis漏单数据
                lack_data = query_redis(redis_key)
                if not lack_data:
                    print("        无漏单数据")
                    continue

                print(f"        找到 {len(lack_data)} 条漏单记录")

                # 使用正确的时间字段键
                time_key = "detectedOpenTime" if state == "send" else "detectedCloseTime"

                # 统计当日漏单
                for order_id, raw_value in lack_data.items():
                    # 解析订单信息
                    order_info = extract_order_info(raw_value)
                    if not order_info:
                        print(f"          订单 {order_id}: 无法解析数据")
                        continue

                    # 获取订单时间
                    order_time = order_info.get(time_key, "")
                    if not order_time:
                        print(f"          订单 {order_id}: 无时间字段")
                        continue

                    # 处理1970-01-01无效时间
                    if "1970-01-01" in order_time:
                        print(f"          订单 {order_id}: 无效时间 ({order_time})")
                        continue

                    # 检查是否是今天
                    if today in order_time:
                        print(f"          √ 订单 {order_id}: 今日漏单 ({order_time})")
                        total_lack_count += 1
                    else:
                        print(f"          订单 {order_id}: 非今日订单 ({order_time})")

    return total_lack_count


if __name__ == '__main__':
    lack_count = count_daily_lack_orders()
    print(f"\n当日漏单总数: {lack_count}")
