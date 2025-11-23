# -*- coding: utf-8 -*-
"""
cron "33 14 * * *" script-path=xxx.py,tag=匹配cron用
new Env('DeepFlood签到')
"""
import os
import time
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from curl_cffi import requests

# ---------------- 通知模块动态加载 ---------------- 
hadsend = False
send = None
try:
    from notify import send
    hadsend = True
except ImportError:
    print("未加载通知模块，跳过通知功能")

# ---------------- 签到逻辑 ---------------- 
def sign(DEEPFLOOD_COOKIE, df_random):
    if not DEEPFLOOD_COOKIE:
        return "invalid", "无有效Cookie"
    
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
        'origin': "https://www.deepflood.com",
        'referer': "https://www.deepflood.com/board",
        'Content-Type': 'application/json',
        'Cookie': DEEPFLOOD_COOKIE
    }
    
    try:
        url = f"https://www.deepflood.com/api/attendance?random={df_random}"
        response = requests.post(url, headers=headers, impersonate="chrome110")
        data = response.json()
        msg = data.get("message", "")
        
        if "鸡腿" in msg or data.get("success"):
            return "success", msg
        elif "已完成签到" in msg:
            return "already", msg
        elif data.get("status") == 404:
            return "invalid", msg
        return "fail", msg
    except Exception as e:
        return "error", str(e)

# ---------------- 查询签到收益统计函数 ---------------- 
def get_signin_stats(DEEPFLOOD_COOKIE, days=30):
    """查询前days天内的签到收益统计"""
    if not DEEPFLOOD_COOKIE:
        return None, "无有效Cookie"
    
    if days <= 0:
        days = 1
    
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
        'origin': "https://www.deepflood.com",
        'referer': "https://www.deepflood.com/board",
        'Cookie': DEEPFLOOD_COOKIE
    }
    
    try:
        # 使用UTC+8时区（上海时区）
        shanghai_tz = ZoneInfo("Asia/Shanghai")
        now_shanghai = datetime.now(shanghai_tz)
        
        # 计算查询开始时间：当前时间减去指定天数
        query_start_time = now_shanghai - timedelta(days=days)
        
        # 获取多页数据以确保覆盖指定天数内的所有数据
        all_records = []
        page = 1
        
        while page <= 10:  # 最多查询10页
            url = f"https://www.deepflood.com/api/account/credit/page-{page}"
            response = requests.get(url, headers=headers, impersonate="chrome110")
            data = response.json()
            
            if not data.get("success") or not data.get("data"):
                break
                
            records = data.get("data", [])
            if not records:
                break
                
            # 检查最后一条记录的时间，如果超出查询范围就停止
            last_record_time = datetime.fromisoformat(
                records[-1][3].replace('Z', '+00:00'))
            last_record_time_shanghai = last_record_time.astimezone(shanghai_tz)
            if last_record_time_shanghai < query_start_time:
                # 只添加在查询范围内的记录
                for record in records:
                    record_time = datetime.fromisoformat(
                        record[3].replace('Z', '+00:00'))
                    record_time_shanghai = record_time.astimezone(shanghai_tz)
                    if record_time_shanghai >= query_start_time:
                        all_records.append(record)
                break
            else:
                all_records.extend(records)
                
            page += 1
            time.sleep(0.5)
        
        # 筛选指定天数内的签到收益记录
        signin_records = []
        for record in all_records:
            amount, balance, description, timestamp = record
            record_time = datetime.fromisoformat(
                timestamp.replace('Z', '+00:00'))
            record_time_shanghai = record_time.astimezone(shanghai_tz)
            
            # 只统计指定天数内的签到收益
            if (record_time_shanghai >= query_start_time and
                    "签到收益" in description and "鸡腿" in description):
                signin_records.append({
                    'amount': amount,
                    'date': record_time_shanghai.strftime('%Y-%m-%d'),
                    'description': description
                })
        
        # 生成时间范围描述
        period_desc = f"近{days}天"
        if days == 1:
            period_desc = "今天"
        
        if not signin_records:
            return {
                'total_amount': 0,
                'average': 0,
                'days_count': 0,
                'records': [],
                'period': period_desc,
            }, f"查询成功，但没有找到{period_desc}的签到记录"
        
        # 统计数据
        total_amount = sum(record['amount'] for record in signin_records)
        days_count = len(signin_records)
        average = round(total_amount / days_count, 2) if days_count > 0 else 0
        
        stats = {
            'total_amount': total_amount,
            'average': average,
            'days_count': days_count,
            'records': signin_records,
            'period': period_desc
        }
        
        return stats, "查询成功"
        
    except Exception as e:
        return None, f"查询异常: {str(e)}"

# ---------------- 显示签到统计信息 ---------------- 
def print_signin_stats(stats, account_name):
    """打印签到统计信息"""
    if not stats:
        return
    
    print(f"\n==== {account_name} 签到收益统计 ({stats['period']}) ====")
    print(f"签到天数: {stats['days_count']} 天")
    print(f"总获得鸡腿: {stats['total_amount']} 个")
    print(f"平均每日鸡腿: {stats['average']} 个")

# ---------------- 时间格式化函数 ---------------- 
def format_time_remaining(seconds):
    """格式化剩余时间显示"""
    if seconds <= 0:
        return "立即执行"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}小时{minutes}分{secs}秒"
    elif minutes > 0:
        return f"{minutes}分{secs}秒"
    else:
        return f"{secs}秒"

# ---------------- 主流程 ---------------- 
if __name__ == "__main__":
    df_random = os.getenv("DF_RANDOM", "true")

    # 读取Cookie
    all_cookies = os.getenv("DEEPFLOOD_COOKIE", "")
    cookie_list = all_cookies.split("&")
    cookie_list = [c.strip() for c in cookie_list if c.strip()]

    print(f"共发现 {len(cookie_list)} 个Cookie")

    if len(cookie_list) == 0:
        print("未找到任何Cookie，请设置DEEPFLOOD_COOKIE环境变量")
        exit(1)

    print(f"\n==== 开始执行签到任务 ====")

    # 执行签到
    for i, cookie in enumerate(cookie_list):
        account_index = i + 1
        display_user = f"账号{account_index}"
        
        print(f"\n==== {display_user} 开始签到 ====")
        print(f"当前时间: {datetime.now().strftime('%H:%M:%S')}")
        
        result, msg = sign(cookie, df_random)

        if result in ["success", "already"]:
            print(f"{display_user} 签到成功: {msg}")
            
            # 查询签到收益统计
            print("正在查询签到收益统计...")
            stats, stats_msg = get_signin_stats(cookie, 30)
            if stats:
                print_signin_stats(stats, display_user)
            else:
                print(f"统计查询失败: {stats_msg}")
            
            # 发送通知（统一格式）
            if hadsend:
                try:
                    notification_msg = f"""🌐 域名：www.deepflood.com

👤 {display_user}：
📝 签到：{msg}"""
                    if stats:
                        notification_msg += f"\n📊 统计：{stats['period']}已签到{stats['days_count']}天，共获得{stats['total_amount']}个鸡腿，平均{stats['average']}个/天"
                    notification_msg += f"\n⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                    send("[DeepFlood]签到成功", notification_msg)
                except Exception as e:
                    print(f"发送通知失败: {e}")
        else:
            print(f"{display_user} 签到失败: {msg}")
            if hadsend:
                try:
                    notification_msg = f"""🌐 域名：www.deepflood.com

👤 {display_user}：
📝 签到：{msg}
⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
                    send("[DeepFlood]签到失败", notification_msg)
                except Exception as e:
                    print(f"发送通知失败: {e}")
    
    print(f"\n==== 所有账号签到完成 ====")
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
