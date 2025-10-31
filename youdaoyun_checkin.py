#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
cron: 0 8 * * *
new Env('有道云笔记签到')
"""

import os
import requests
import json
import random
import time
from datetime import datetime, timedelta

# ---------------- 统一通知模块加载 ----------------
hadsend = False
send = None
try:
    from notify import send
    hadsend = True
    print("✅ 已加载notify.py通知模块")
except ImportError:
    print("⚠️  未加载通知模块，跳过通知功能")

# 配置项
YOUDAO_COOKIE = os.environ.get('YOUDAO_COOKIE', '')
max_random_delay = int(os.getenv("MAX_RANDOM_DELAY", "3600"))
random_signin = os.getenv("RANDOM_SIGNIN", "true").lower() == "true"
privacy_mode = os.getenv("PRIVACY_MODE", "true").lower() == "true"

def format_time_remaining(seconds):
    """格式化时间显示"""
    if seconds <= 0:
        return "立即执行"
    hours, minutes = divmod(seconds, 3600)
    minutes, secs = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}小时{minutes}分{secs}秒"
    elif minutes > 0:
        return f"{minutes}分{secs}秒"
    else:
        return f"{secs}秒"

def wait_with_countdown(delay_seconds, task_name):
    """带倒计时的随机延迟等待"""
    if delay_seconds <= 0:
        return
    print(f"{task_name} 需要等待 {format_time_remaining(delay_seconds)}")
    remaining = delay_seconds
    while remaining > 0:
        if remaining <= 10 or remaining % 10 == 0:
            print(f"{task_name} 倒计时: {format_time_remaining(remaining)}")
        sleep_time = 1 if remaining <= 10 else min(10, remaining)
        time.sleep(sleep_time)
        remaining -= sleep_time

def notify_user(title, content):
    """统一通知函数"""
    if hadsend:
        try:
            send(title, content)
            print(f"✅ 通知发送完成: {title}")
        except Exception as e:
            print(f"❌ 通知发送失败: {e}")
    else:
        print(f"📢 {title}\n📄 {content}")

def mask_uid(uid):
    """UID脱敏处理"""
    if not uid or uid == "未知用户":
        return uid

    if privacy_mode and len(uid) > 6:
        return f"{uid[:3]}***{uid[-3:]}"
    return uid

class YouDaoYun:
    name = "有道云笔记"

    def __init__(self, cookie: str, index: int = 1):
        self.cookie = cookie
        self.index = index
        self.cookies_dict = {}
        self.uid = "未知用户"

    def parse_cookie(self):
        """解析cookie字符串为字典"""
        try:
            for item in self.cookie.split("; "):
                if "=" in item:
                    key, value = item.split("=", 1)
                    self.cookies_dict[key] = value

            # 获取用户ID
            ynote_pers = self.cookies_dict.get("YNOTE_PERS", "")
            if ynote_pers:
                parts = ynote_pers.split("||")
                if len(parts) >= 2:
                    self.uid = parts[-2]

            print(f"👤 用户ID: {mask_uid(self.uid)}")
            return True
        except Exception as e:
            print(f"❌ Cookie解析失败: {e}")
            return False

    def refresh_cookies(self):
        """刷新cookies"""
        try:
            print("🔄 正在刷新cookies...")
            response = requests.get(
                "http://note.youdao.com/login/acc/pe/getsess?product=YNOTE",
                cookies=self.cookies_dict,
                timeout=15
            )

            if response.status_code == 200:
                # 更新cookies
                self.cookies_dict.update(dict(response.cookies))
                print("✅ Cookies刷新成功")
                return True
            else:
                print(f"⚠️ Cookies刷新失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cookies刷新异常: {e}")
            return False

    def sync_promotion(self):
        """同步推广空间"""
        try:
            print("📝 正在同步推广...")
            url = "https://note.youdao.com/yws/api/daupromotion?method=sync"
            response = requests.post(url=url, cookies=self.cookies_dict, timeout=15)

            if response.status_code == 200:
                data = response.json()
                if "error" not in response.text and "reward" in response.text:
                    sync_space = data.get("rewardSpace", 0) // 1048576  # 转换为MB
                    print(f"✅ 同步推广成功，获得空间: {sync_space}M")
                    return sync_space
                else:
                    error_msg = data.get("error", "未知错误")
                    print(f"⚠️ 同步推广失败: {error_msg}")
                    return 0
            else:
                print(f"❌ 同步推广请求失败，状态码: {response.status_code}")
                return 0
        except Exception as e:
            print(f"❌ 同步推广异常: {e}")
            return 0

    def daily_checkin(self):
        """每日签到"""
        try:
            print("📝 正在执行每日签到...")
            url = "https://note.youdao.com/yws/mapi/user?method=checkin"
            response = requests.post(url=url, cookies=self.cookies_dict, timeout=15)

            if response.status_code == 200:
                data = response.json()
                checkin_space = data.get("space", 0) // 1048576  # 转换为MB
                print(f"✅ 每日签到成功，获得空间: {checkin_space}M")
                return checkin_space
            else:
                print(f"❌ 每日签到失败，状态码: {response.status_code}")
                return 0
        except Exception as e:
            print(f"❌ 每日签到异常: {e}")
            return 0

    def watch_ads(self, count=3):
        """观看广告获取空间"""
        total_ad_space = 0
        try:
            print(f"📺 正在观看广告（共{count}次）...")
            url = "https://note.youdao.com/yws/mapi/user?method=adRandomPrompt"

            for i in range(count):
                response = requests.post(url=url, cookies=self.cookies_dict, timeout=15)

                if response.status_code == 200:
                    data = response.json()
                    ad_space = data.get("space", 0) // 1048576  # 转换为MB
                    total_ad_space += ad_space
                    print(f"  第{i+1}次观看广告，获得空间: {ad_space}M")

                    # 随机延迟，模拟真实观看
                    if i < count - 1:
                        time.sleep(random.uniform(1, 3))
                else:
                    print(f"  第{i+1}次观看广告失败，状态码: {response.status_code}")

            print(f"✅ 观看广告完成，总计获得: {total_ad_space}M")
            return total_ad_space
        except Exception as e:
            print(f"❌ 观看广告异常: {e}")
            return total_ad_space

    def main(self):
        """主执行函数"""
        print(f"\n==== 有道云笔记账号{self.index} 开始签到 ====")

        if not self.cookie.strip():
            error_msg = """Cookie配置错误

❌ 错误原因: 未找到YOUDAO_COOKIE环境变量

🔧 解决方法:
1. 打开有道云笔记网页版: https://note.youdao.com/
2. 登录您的账号
3. 按F12打开开发者工具
4. 切换到Network标签页，刷新页面
5. 找到任意请求的Request Headers
6. 复制完整的Cookie值
7. 在青龙面板中添加环境变量YOUDAO_COOKIE
"""

            print(f"❌ {error_msg}")
            return error_msg, False

        # 1. 解析Cookie
        if not self.parse_cookie():
            return "Cookie解析失败", False

        # 2. 刷新Cookies
        if not self.refresh_cookies():
            return "Cookies刷新失败，请更新Cookie", False

        # 3. 同步推广空间
        sync_space = self.sync_promotion()

        # 4. 每日签到
        checkin_space = self.daily_checkin()

        # 5. 观看广告
        ad_space = self.watch_ads(count=3)

        # 6. 计算总空间
        total_space = sync_space + checkin_space + ad_space

        # 7. 组合结果消息
        final_msg = f"""🌟 有道云笔记签到结果

👤 账号: {mask_uid(self.uid)}
📦 空间奖励: +{total_space}M"""

        if sync_space > 0:
            final_msg += f"\n  └ 同步推广: {sync_space}M"
        if checkin_space > 0:
            final_msg += f"\n  └ 每日签到: {checkin_space}M"
        if ad_space > 0:
            final_msg += f"\n  └ 观看广告: {ad_space}M"

        final_msg += f"\n⏰ 时间: {datetime.now().strftime('%m-%d %H:%M')}"

        is_success = total_space > 0
        print(f"{'✅ 签到成功' if is_success else '⚠️  签到失败'}")
        return final_msg, is_success

def main():
    """主程序入口"""
    print(f"==== 有道云笔记签到开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====")

    # 显示配置状态
    print(f"🔒 隐私保护模式: {'已启用' if privacy_mode else '已禁用'}")

    # 随机延迟（整体延迟）
    if random_signin:
        delay_seconds = random.randint(0, max_random_delay)
        if delay_seconds > 0:
            print(f"🎲 随机延迟: {format_time_remaining(delay_seconds)}")
            wait_with_countdown(delay_seconds, "有道云笔记签到")

    # 获取Cookie配置
    youdao_cookies = YOUDAO_COOKIE

    if not youdao_cookies:
        error_msg = """❌ 未找到YOUDAO_COOKIE环境变量

🔧 获取Cookie的方法:
1. 打开有道云笔记网页版: https://note.youdao.com/
2. 登录您的账号
3. 按F12打开开发者工具
4. 切换到Network标签页，刷新页面
5. 找到任意请求的Request Headers
6. 复制完整的Cookie值
7. 在青龙面板中添加环境变量YOUDAO_COOKIE
"""

        print(error_msg)
        notify_user("有道云笔记签到失败", error_msg)
        return

    # 支持多账号（用换行分隔）
    if '\n' in youdao_cookies:
        cookies = [cookie.strip() for cookie in youdao_cookies.split('\n') if cookie.strip()]
    else:
        cookies = [youdao_cookies.strip()]

    print(f"📝 共发现 {len(cookies)} 个账号")

    success_count = 0
    total_count = len(cookies)
    results = []

    for index, cookie in enumerate(cookies):
        try:
            # 账号间随机等待
            if index > 0:
                delay = random.uniform(5, 15)
                print(f"⏱️  随机等待 {delay:.1f} 秒后处理下一个账号...")
                time.sleep(delay)

            # 执行签到
            youdao = YouDaoYun(cookie, index + 1)
            result_msg, is_success = youdao.main()

            if is_success:
                success_count += 1

            results.append({
                'index': index + 1,
                'success': is_success,
                'message': result_msg
            })

            # 发送单个账号通知
            status = "成功" if is_success else "失败"
            title = f"有道云笔记账号{index + 1}签到{status}"
            notify_user(title, result_msg)

        except Exception as e:
            error_msg = f"账号{index + 1}: 执行异常 - {str(e)}"
            print(f"❌ {error_msg}")
            notify_user(f"有道云笔记账号{index + 1}签到失败", error_msg)

    # 发送汇总通知
    if total_count > 1:
        summary_msg = f"""📊 有道云笔记签到汇总

📈 总计: {total_count}个账号
✅ 成功: {success_count}个
❌ 失败: {total_count - success_count}个
📊 成功率: {success_count/total_count*100:.1f}%
⏰ 完成时间: {datetime.now().strftime('%m-%d %H:%M')}"""

        # 添加详细结果（最多显示5个账号的详情）
        if len(results) <= 5:
            summary_msg += "\n\n📋 详细结果:"
            for result in results:
                status_icon = "✅" if result['success'] else "❌"
                summary_msg += f"\n{status_icon} 账号{result['index']}"

        notify_user("有道云笔记签到汇总", summary_msg)

    print(f"\n==== 有道云笔记签到完成 - 成功{success_count}/{total_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====")

def handler(event, context):
    """云函数入口"""
    main()

if __name__ == "__main__":
    main()
