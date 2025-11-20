#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
cron: 0 8 * * *
new Env('有道云笔记签到')
"""

import os
import sys
import io

# 设置标准输出编码为UTF-8（解决Windows环境emoji显示问题）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import random
import time
from datetime import datetime

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
YOUDAO_DOMAIN = (os.getenv("YOUDAO_DOMAIN") or "https://note.youdao.com").rstrip("/")
YOUDAO_COOKIE = os.environ.get('YOUDAO_COOKIE', '')
max_random_delay = int(os.getenv("MAX_RANDOM_DELAY", "3600"))
random_signin = os.getenv("RANDOM_SIGNIN", "true").lower() == "true"

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

class YouDaoYun:
    name = "有道云笔记"

    def __init__(self, cookie: str, index: int = 1):
        self.cookie = cookie
        self.index = index
        self.cookies_dict = {}
        self.uid = "未知用户"

    @staticmethod
    def format_size(size_bytes):
        """将字节转换为可读格式"""
        if size_bytes >= 1073741824:  # >= 1GB
            return f"{size_bytes / 1073741824:.2f}GB"
        elif size_bytes >= 1048576:  # >= 1MB
            return f"{size_bytes / 1048576:.2f}MB"
        else:
            return f"{size_bytes / 1024:.2f}KB"

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

            print(f"👤 用户ID: {self.uid}")
            return True
        except Exception as e:
            print(f"❌ Cookie解析失败: {e}")
            return False

    def refresh_cookies(self):
        """刷新cookies"""
        try:
            print("🔄 正在刷新cookies...")
            response = requests.get(
                f"{YOUDAO_DOMAIN}/login/acc/pe/getsess?product=YNOTE",
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

    def get_user_space_info(self):
        """获取用户存储空间信息"""
        try:
            print("📊 正在获取存储空间信息...")
            url = f"{YOUDAO_DOMAIN}/yws/mapi/payment?method=status&pversion=v2"

            cstk = self.cookies_dict.get('YNOTE_CSTK', '')
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/plain, */*'
            }
            data = {"cstk": cstk}

            response = requests.post(
                url=url,
                json=data,
                cookies=self.cookies_dict,
                headers=headers,
                timeout=15
            )

            if response.status_code == 200:
                result = response.json()

                if "um" in result:
                    um = result["um"]
                    total_size = um.get("q", 0)  # 总容量（字节）
                    used_size = um.get("u", 0)   # 已用空间（字节）

                    space_info = {
                        "total_size": total_size,
                        "used_size": used_size,
                        "total_formatted": self.format_size(total_size),
                        "used_formatted": self.format_size(used_size),
                        "free_formatted": self.format_size(total_size - used_size)
                    }

                    print(f"✅ 存储空间信息获取成功")
                    print(f"   总容量: {space_info['total_formatted']}")
                    print(f"   已使用: {space_info['used_formatted']}")
                    print(f"   剩余: {space_info['free_formatted']}")

                    return space_info
                else:
                    print(f"⚠️ 响应中未找到空间信息")
                    return {}
            else:
                print(f"⚠️ 获取存储空间信息失败，状态码: {response.status_code}")
                return {}
        except Exception as e:
            print(f"❌ 获取存储空间信息异常: {e}")
            return {}

    def sync_promotion(self):
        """同步推广空间"""
        try:
            print("📝 正在同步推广...")
            url = f"{YOUDAO_DOMAIN}/yws/api/daupromotion?method=sync"
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
            url = f"{YOUDAO_DOMAIN}/yws/mapi/user?method=checkin"
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
            url = f"{YOUDAO_DOMAIN}/yws/mapi/user?method=adRandomPrompt"

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
            error_msg = "Cookie为空，请检查配置"
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

        # 7. 获取用户存储空间信息（签到后获取，包含签到奖励）
        space_info = self.get_user_space_info()

        # 8. 组合结果消息（统一模板格式）
        domain_display = YOUDAO_DOMAIN.replace('https://', '').replace('http://', '')
        final_msg = f"""🌐 域名：{domain_display}

👤 账号{self.index}：
📱 用户：{self.uid}"""

        # 添加存储空间信息
        if space_info:
            final_msg += f"""
💾 空间：总容量 {space_info['total_formatted']}，已使用 {space_info['used_formatted']}"""

        final_msg += f"""
📝 签到：签到完成，获得 {total_space}M 空间"""

        if total_space > 0:
            final_msg += "\n💡 明细："
            if sync_space > 0:
                final_msg += f" 同步推广{sync_space}M"
            if checkin_space > 0:
                final_msg += f" 每日签到{checkin_space}M"
            if ad_space > 0:
                final_msg += f" 观看广告{ad_space}M"

        final_msg += f"\n⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        is_success = total_space > 0
        print(f"{'✅ 签到成功' if is_success else '⚠️  签到失败'}")
        return final_msg, is_success

def main():
    """主程序入口"""
    print(f"==== 有道云笔记签到开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====")

    # 随机延迟（整体延迟）
    if random_signin:
        delay_seconds = random.randint(0, max_random_delay)
        if delay_seconds > 0:
            print(f"🎲 随机延迟: {format_time_remaining(delay_seconds)}")
            wait_with_countdown(delay_seconds, "有道云笔记签到")

    # 获取Cookie配置
    if not YOUDAO_COOKIE:
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
    if '\n' in YOUDAO_COOKIE:
        cookies = [cookie.strip() for cookie in YOUDAO_COOKIE.split('\n') if cookie.strip()]
    else:
        cookies = [YOUDAO_COOKIE.strip()]

    print(f"📝 共发现 {len(cookies)} 个账号")

    success_count = 0
    total_count = len(cookies)

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

            # 发送单个账号通知（统一标题格式）
            status = "成功" if is_success else "失败"
            title = f"[有道云笔记]签到{status}"
            notify_user(title, result_msg)

        except Exception as e:
            error_msg = f"账号{index + 1}: 执行异常 - {str(e)}"
            print(f"❌ {error_msg}")
            notify_user(f"有道云笔记账号{index + 1}签到失败", error_msg)

    # 发送汇总通知（统一格式）
    if total_count > 1:
        domain_display = YOUDAO_DOMAIN.replace('https://', '').replace('http://', '')
        summary_msg = f"""🌐 域名：{domain_display}

📊 签到汇总：
✅ 成功：{success_count}个
❌ 失败：{total_count - success_count}个
📈 成功率：{success_count/total_count*100:.1f}%
⏰ 完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        notify_user("[有道云笔记]签到汇总", summary_msg)

    print(f"\n==== 有道云笔记签到完成 - 成功{success_count}/{total_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====")

def handler(event, context):
    """云函数入口"""
    main()

if __name__ == "__main__":
    main()
