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

# 时区支持
try:
    from zoneinfo import ZoneInfo
    BEIJING_TZ = ZoneInfo("Asia/Shanghai")
except ImportError:
    BEIJING_TZ = None

# ---------------- 日志类 ----------------
class Logger:
    def __init__(self):
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"

    def log(self, level, message):
        if BEIJING_TZ:
            timestamp = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[{timestamp}] [{level}] {message}"
        print(formatted_msg)

    def info(self, message):
        self.log("INFO", message)

    def warning(self, message):
        self.log("WARNING", message)

    def error(self, message):
        self.log("ERROR", message)

    def debug(self, message):
        if self.debug_mode:
            self.log("DEBUG", message)

logger = Logger()

# ---------------- 时区辅助函数 ----------------
def now_beijing():
    """获取北京时间"""
    if BEIJING_TZ:
        return datetime.now(BEIJING_TZ)
    else:
        return datetime.now()

# ---------------- 统一通知模块加载 ----------------
hadsend = False
send = None
try:
    from notify import send
    hadsend = True
    logger.info("已加载notify.py通知模块")
except ImportError:
    logger.info("未加载通知模块，跳过通知功能")

# ---------------- 配置项 ----------------
YOUDAO_DOMAIN = (os.getenv("YOUDAO_DOMAIN") or "https://note.youdao.com").rstrip("/")
YOUDAO_COOKIE = os.environ.get('YOUDAO_COOKIE', '')

# ---------------- 统一通知函数 ----------------
def safe_send_notify(title, content):
    """统一通知函数"""
    if hadsend:
        try:
            send(title, content)
            logger.info(f"通知推送成功: {title}")
        except Exception as e:
            logger.error(f"通知推送失败: {e}")
    else:
        logger.info(f"通知: {title}")

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
        logger.info("开始解析Cookie...")
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

            logger.info(f"Cookie解析成功，用户ID: {self.uid}")
            return True
        except Exception as e:
            logger.error(f"Cookie解析失败，原因: {e}")
            return False

    def refresh_cookies(self):
        """刷新cookies"""
        logger.info("开始刷新Cookies...")
        try:
            url = f"{YOUDAO_DOMAIN}/login/acc/pe/getsess?product=YNOTE"
            response = requests.get(
                url,
                cookies=self.cookies_dict,
                timeout=15
            )

            logger.debug(f"API 请求：GET {url} {response.status_code}")
            logger.debug(f"响应：{response.text[:300]}")

            if response.status_code == 200:
                # 更新cookies
                self.cookies_dict.update(dict(response.cookies))
                logger.info("Cookies刷新成功")
                return True
            else:
                logger.warning(f"Cookies刷新失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Cookies刷新异常: {e}")
            return False

    def get_user_space_info(self):
        """获取用户存储空间信息"""
        logger.info("开始获取存储空间信息...")
        try:
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

            logger.debug(f"API 请求：POST {url} {response.status_code}")
            logger.debug(f"响应：{response.text[:300]}")

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

                    logger.info(f"存储空间信息获取成功 - 总容量: {space_info['total_formatted']}, 已使用: {space_info['used_formatted']}, 剩余: {space_info['free_formatted']}")
                    return space_info
                else:
                    logger.warning("响应中未找到空间信息")
                    return {}
            else:
                logger.warning(f"获取存储空间信息失败，状态码: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"获取存储空间信息异常: {e}")
            return {}

    def sync_promotion(self):
        """同步推广空间"""
        logger.info("开始同步推广...")
        try:
            url = f"{YOUDAO_DOMAIN}/yws/api/daupromotion?method=sync"
            response = requests.post(url=url, cookies=self.cookies_dict, timeout=15)

            logger.debug(f"API 请求：POST {url} {response.status_code}")
            logger.debug(f"响应：{response.text[:300]}")

            if response.status_code == 200:
                data = response.json()
                if "error" not in response.text and "reward" in response.text:
                    sync_space = data.get("rewardSpace", 0) // 1048576  # 转换为MB
                    logger.info(f"同步推广成功，获得空间: {sync_space}M")
                    return sync_space
                else:
                    error_msg = data.get("error", "未知错误")
                    logger.warning(f"同步推广失败: {error_msg}")
                    return 0
            else:
                logger.error(f"同步推广请求失败，状态码: {response.status_code}")
                return 0
        except Exception as e:
            logger.error(f"同步推广异常: {e}")
            return 0

    def daily_checkin(self):
        """每日签到"""
        logger.info("开始执行每日签到...")
        try:
            url = f"{YOUDAO_DOMAIN}/yws/mapi/user?method=checkin"
            response = requests.post(url=url, cookies=self.cookies_dict, timeout=15)

            logger.debug(f"API 请求：POST {url} {response.status_code}")
            logger.debug(f"响应：{response.text[:300]}")

            if response.status_code == 200:
                data = response.json()
                checkin_space = data.get("space", 0) // 1048576  # 转换为MB
                logger.info(f"每日签到成功，获得空间: {checkin_space}M")
                return checkin_space
            else:
                logger.error(f"每日签到失败，状态码: {response.status_code}")
                return 0
        except Exception as e:
            logger.error(f"每日签到异常: {e}")
            return 0

    def watch_ads(self, count=3):
        """观看广告获取空间"""
        logger.info(f"开始观看广告（共{count}次）...")
        total_ad_space = 0
        try:
            url = f"{YOUDAO_DOMAIN}/yws/mapi/user?method=adRandomPrompt"

            for i in range(count):
                response = requests.post(url=url, cookies=self.cookies_dict, timeout=15)

                logger.debug(f"API 请求：POST {url} {response.status_code}")
                logger.debug(f"响应：{response.text[:300]}")

                if response.status_code == 200:
                    data = response.json()
                    ad_space = data.get("space", 0) // 1048576  # 转换为MB
                    total_ad_space += ad_space
                    logger.info(f"第{i+1}次观看广告，获得空间: {ad_space}M")

                    # 随机延迟，模拟真实观看
                    if i < count - 1:
                        time.sleep(random.uniform(1, 3))
                else:
                    logger.warning(f"第{i+1}次观看广告失败，状态码: {response.status_code}")

            logger.info(f"观看广告完成，总计获得: {total_ad_space}M")
            return total_ad_space
        except Exception as e:
            logger.error(f"观看广告异常: {e}")
            return total_ad_space

    def main(self):
        """主执行函数"""
        logger.info(f"\n==== 有道云笔记账号{self.index} 开始签到 ====")

        if not self.cookie.strip():
            error_msg = "Cookie为空，请检查配置"
            logger.error(error_msg)
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

        final_msg += f"\n⏰ 时间：{now_beijing().strftime('%Y-%m-%d %H:%M:%S')}"

        is_success = total_space > 0
        if is_success:
            logger.info("签到成功")
        else:
            logger.warning("签到失败")
        return final_msg, is_success

def main():
    """主程序入口"""
    logger.info(f"==== 有道云笔记签到开始 - {now_beijing().strftime('%Y-%m-%d %H:%M:%S')} ====")

    # 获取Cookie配置
    if not YOUDAO_COOKIE:
        error_msg = "未找到YOUDAO_COOKIE环境变量，请查看 README.md 配置说明"
        logger.error(error_msg)
        safe_send_notify("[有道云笔记]签到失败", error_msg)
        return

    # 支持多账号（用换行分隔）
    if '\n' in YOUDAO_COOKIE:
        cookies = [cookie.strip() for cookie in YOUDAO_COOKIE.split('\n') if cookie.strip()]
    else:
        cookies = [YOUDAO_COOKIE.strip()]

    logger.info(f"共发现 {len(cookies)} 个账号")

    success_count = 0
    total_count = len(cookies)

    for index, cookie in enumerate(cookies):
        try:
            # 账号间随机等待
            if index > 0:
                delay = random.uniform(5, 15)
                logger.info(f"随机等待 {delay:.1f} 秒后处理下一个账号...")
                time.sleep(delay)

            # 执行签到
            youdao = YouDaoYun(cookie, index + 1)
            result_msg, is_success = youdao.main()

            if is_success:
                success_count += 1

            # 发送单个账号通知（统一标题格式）
            status = "成功" if is_success else "失败"
            title = f"[有道云笔记]签到{status}"
            safe_send_notify(title, result_msg)

        except Exception as e:
            error_msg = f"账号{index + 1}: 执行异常 - {str(e)}"
            logger.error(error_msg)
            safe_send_notify(f"[有道云笔记]账号{index + 1}签到失败", error_msg)

    # 发送汇总通知（统一格式）
    if total_count > 1:
        domain_display = YOUDAO_DOMAIN.replace('https://', '').replace('http://', '')
        summary_msg = f"""🌐 域名：{domain_display}

📊 签到汇总：
✅ 成功：{success_count}个
❌ 失败：{total_count - success_count}个
📈 成功率：{success_count/total_count*100:.1f}%
⏰ 完成时间：{now_beijing().strftime('%Y-%m-%d %H:%M:%S')}"""

        safe_send_notify("[有道云笔记]签到汇总", summary_msg)

    logger.info(f"\n==== 有道云笔记签到完成 - 成功{success_count}/{total_count} - {now_beijing().strftime('%Y-%m-%d %H:%M:%S')} ====")

def handler(event, context):
    """云函数入口"""
    main()

if __name__ == "__main__":
    main()
