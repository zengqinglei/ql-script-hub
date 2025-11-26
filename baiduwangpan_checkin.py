#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
cron: 0 9 * * *
new Env('百度网盘签到')
"""

import sys
import io

# 设置标准输出编码为UTF-8（解决Windows环境emoji显示问题）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import time
import re
import requests
import random
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

# 配置项
BAIDU_DOMAIN = (os.getenv("BAIDU_DOMAIN") or "https://pan.baidu.com").rstrip("/")
BAIDU_COOKIE = os.environ.get('BAIDU_COOKIE', '')

HEADERS = {
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 '
        'Safari/537.36'
    ),
    'X-Requested-With': 'XMLHttpRequest',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': f'{BAIDU_DOMAIN}/wap/svip/growth/task',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
}

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

class BaiduPan:
    name = "百度网盘"

    def __init__(self, cookie: str, index: int = 1):
        self.cookie = cookie
        self.index = index
        self.final_messages = []

    def add_message(self, msg: str):
        """统一收集消息并打印"""
        logger.info(msg)
        self.final_messages.append(msg)

    def signin(self):
        """执行每日签到"""
        if not self.cookie.strip():
            self.add_message("未检测到 BAIDU_COOKIE，请检查配置")
            return False, "Cookie配置错误"

        logger.info("开始签到...")
        url = f"{BAIDU_DOMAIN}/rest/2.0/membership/level?app_id=250528&web=5&method=signin"
        signed_headers = HEADERS.copy()
        signed_headers['Cookie'] = self.cookie

        try:
            resp = requests.get(url, headers=signed_headers, timeout=15)
            logger.debug(f"API 请求：GET {url} {resp.status_code}")
            logger.debug(f"响应：{resp.text[:300]}")

            if resp.status_code == 200:
                sign_point = re.search(r'points":(\d+)', resp.text)
                signin_error_msg = re.search(r'"error_msg":"(.*?)"', resp.text)

                if sign_point:
                    points = sign_point.group(1)
                    self.add_message(f"签到成功，获得积分: {points}")
                    logger.info(f"今日奖励: {points}积分")
                    return True, f"签到成功，获得{points}积分"
                else:
                    # 检查是否有错误信息
                    if signin_error_msg and signin_error_msg.group(1):
                        error_msg = signin_error_msg.group(1)
                        if any(keyword in error_msg for keyword in ["已签到", "重复签到", "not allow"]):
                            self.add_message("今日已签到")
                            return True, "今日已签到"
                        else:
                            self.add_message(f"签到失败: {error_msg}")
                            return False, f"签到失败: {error_msg}"
                    else:
                        self.add_message("签到成功，但未检索到积分信息")
                        return True, "签到成功"
            else:
                error_msg = f"签到失败，状态码: {resp.status_code}"
                self.add_message(error_msg)
                return False, error_msg

        except requests.exceptions.Timeout:
            error_msg = "签到请求超时"
            self.add_message(error_msg)
            return False, error_msg
        except requests.exceptions.ConnectionError:
            error_msg = "网络连接错误"
            self.add_message(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"签到请求异常: {e}"
            self.add_message(error_msg)
            return False, error_msg

    def get_daily_question(self):
        """获取日常问题"""
        if not self.cookie.strip():
            return None, None

        logger.info("开始获取每日问题...")
        url = f"{BAIDU_DOMAIN}/act/v2/membergrowv2/getdailyquestion?app_id=250528&web=5"
        signed_headers = HEADERS.copy()
        signed_headers['Cookie'] = self.cookie

        try:
            resp = requests.get(url, headers=signed_headers, timeout=15)
            logger.debug(f"API 请求：GET {url} {resp.status_code}")
            logger.debug(f"响应：{resp.text[:300]}")

            if resp.status_code == 200:
                answer = re.search(r'"answer":(\d+)', resp.text)
                ask_id = re.search(r'"ask_id":(\d+)', resp.text)
                question = re.search(r'"question":"(.*?)"', resp.text)

                if answer and ask_id:
                    if question:
                        logger.info(f"今日问题: {question.group(1)}")
                        logger.info(f"答案: {answer.group(1)}")
                    return answer.group(1), ask_id.group(1)
                else:
                    self.add_message("未找到日常问题或答案")
            else:
                self.add_message(f"获取日常问题失败，状态码: {resp.status_code}")
        except Exception as e:
            self.add_message(f"获取问题请求异常: {e}")
        return None, None

    def answer_question(self, answer, ask_id):
        """回答每日问题"""
        if not self.cookie.strip():
            return False, "Cookie配置错误"

        logger.info("开始回答每日问题...")
        url = (
            f"{BAIDU_DOMAIN}/act/v2/membergrowv2/answerquestion"
            f"?app_id=250528&web=5&ask_id={ask_id}&answer={answer}"
        )
        signed_headers = HEADERS.copy()
        signed_headers['Cookie'] = self.cookie

        try:
            resp = requests.get(url, headers=signed_headers, timeout=15)
            logger.debug(f"API 请求：GET {url} {resp.status_code}")
            logger.debug(f"响应：{resp.text[:300]}")

            if resp.status_code == 200:
                answer_msg = re.search(r'"show_msg":"(.*?)"', resp.text)
                answer_score = re.search(r'"score":(\d+)', resp.text)

                if answer_score:
                    score = answer_score.group(1)
                    self.add_message(f"答题成功，获得积分: {score}")
                    logger.info(f"答题奖励: {score}积分")
                    return True, f"答题成功，获得{score}积分"
                else:
                    # 检查答题信息
                    if answer_msg and answer_msg.group(1):
                        msg = answer_msg.group(1)
                        if any(keyword in msg for keyword in ["已回答", "exceeded", "超出", "超限"]):
                            self.add_message("今日已答题或次数已用完")
                            return True, "今日已答题"
                        else:
                            self.add_message(f"答题失败: {msg}")
                            return False, f"答题失败: {msg}"
                    else:
                        self.add_message("答题成功，但未检索到积分信息")
                        return True, "答题成功"
            else:
                error_msg = f"答题失败，状态码: {resp.status_code}"
                self.add_message(error_msg)
                return False, error_msg
        except Exception as e:
            error_msg = f"答题请求异常: {e}"
            self.add_message(error_msg)
            return False, error_msg

    def get_storage_info(self):
        """获取存储空间信息"""
        if not self.cookie.strip():
            return None

        logger.info("开始获取存储空间信息...")
        url = f"{BAIDU_DOMAIN}/api/quota?clienttype=0&app_id=250528&web=1"
        signed_headers = HEADERS.copy()
        signed_headers['Cookie'] = self.cookie

        try:
            resp = requests.get(url, headers=signed_headers, timeout=15)
            logger.debug(f"API 请求：GET {url} {resp.status_code}")
            logger.debug(f"响应：{resp.text[:300]}")

            if resp.status_code == 200:
                data = resp.json()
                if data.get('errno') == 0:
                    total_bytes = data.get('total', 0)
                    used_bytes = data.get('used', 0)

                    # 转换为GB
                    total_gb = round(total_bytes / (1024**3), 2)
                    used_gb = round(used_bytes / (1024**3), 2)

                    if total_gb > 0:
                        usage_percent = round((used_gb / total_gb) * 100, 1)
                        logger.info(f"存储空间: {used_gb}GB / {total_gb}GB ({usage_percent}%)")
                        return {
                            'used_gb': used_gb,
                            'total_gb': total_gb,
                            'usage_percent': usage_percent
                        }
                else:
                    logger.warning(f"获取存储信息失败，errno: {data.get('errno')}")
            else:
                logger.warning(f"获取存储信息失败，状态码: {resp.status_code}")
        except Exception as e:
            logger.warning(f"存储信息请求异常: {e}")

        return None

    def get_user_info(self):
        """获取用户信息"""
        if not self.cookie.strip():
            return "未知用户", "未知", "未知", "未知"

        logger.info("开始获取用户信息...")

        # 获取用户名（使用uinfo API）
        user = "未知用户"
        try:
            uinfo_url = f"{BAIDU_DOMAIN}/rest/2.0/xpan/nas?method=uinfo"
            uinfo_headers = HEADERS.copy()
            uinfo_headers['Cookie'] = self.cookie
            uinfo_resp = requests.get(uinfo_url, headers=uinfo_headers, timeout=15)
            logger.debug(f"API 请求：GET {uinfo_url} {uinfo_resp.status_code}")
            logger.debug(f"响应：{uinfo_resp.text[:300]}")

            if uinfo_resp.status_code == 200:
                uinfo_data = uinfo_resp.json()
                if uinfo_data.get('errno') == 0:
                    user = uinfo_data.get('baidu_name', '未知用户')
                    if not user:
                        user = uinfo_data.get('netdisk_name', '未知用户')
        except Exception as e:
            logger.warning(f"获取用户名失败: {e}")

        # 获取会员信息
        url = f"{BAIDU_DOMAIN}/rest/2.0/membership/user?app_id=250528&web=5&method=query"
        signed_headers = HEADERS.copy()
        signed_headers['Cookie'] = self.cookie

        try:
            resp = requests.get(url, headers=signed_headers, timeout=15)
            logger.debug(f"API 请求：GET {url} {resp.status_code}")
            logger.debug(f"响应：{resp.text[:300]}")

            if resp.status_code == 200:
                current_value = re.search(r'current_value":(\d+)', resp.text)
                current_level = re.search(r'current_level":(\d+)', resp.text)
                vip_type = re.search(r'"vip_type":(\d+)', resp.text)

                level = current_level.group(1) if current_level else "未知"
                value = current_value.group(1) if current_value else "未知"

                # VIP类型解析
                vip_status = "普通用户"
                if vip_type:
                    vip_code = int(vip_type.group(1))
                    if vip_code == 1:
                        vip_status = "普通会员"
                    elif vip_code == 2:
                        vip_status = "超级会员"
                    elif vip_code == 3:
                        vip_status = "至尊会员"

                level_msg = f"当前会员等级: Lv.{level}，成长值: {value}，会员类型: {vip_status}"
                self.add_message(level_msg)

                logger.info(f"用户: {user}")
                logger.info(f"等级: Lv.{level}")
                logger.info(f"成长值: {value}")
                logger.info(f"会员: {vip_status}")

                return user, level, value, vip_status
            else:
                self.add_message(f"获取用户信息失败，状态码: {resp.status_code}")
                return "未知用户", "未知", "未知", "未知"
        except Exception as e:
            self.add_message(f"用户信息请求异常: {e}")
            return "未知用户", "未知", "未知", "未知"

    def main(self):
        """主执行函数"""
        logger.info(f"==== 百度网盘账号{self.index} 开始签到 ====")

        if not self.cookie.strip():
            error_msg = "Cookie配置错误，请查看 README.md 配置说明"
            logger.error(error_msg)
            return error_msg, False

        # 1. 执行签到
        signin_success, signin_msg = self.signin()

        # 2. 随机等待
        time.sleep(random.uniform(2, 5))

        # 3. 获取并回答每日问题
        answer_success = False
        answer_msg = ""
        answer, ask_id = self.get_daily_question()
        if answer and ask_id:
            answer_success, answer_msg = self.answer_question(answer, ask_id)

        # 4. 获取存储空间信息（签到后获取）
        storage_info = self.get_storage_info()

        # 5. 获取用户信息（签到后获取，包含签到和答题后的成长值）
        user, level, value, vip_status = self.get_user_info()

        # 6. 组合结果消息（统一模板格式）
        final_msg = f"""🌐 域名：{BAIDU_DOMAIN.replace('https://', '').replace('http://', '')}

👤 账号{self.index}：
📱 用户：{user}
💎 会员：{vip_status}，Lv.{level}（{value}成长值）"""

        if storage_info:
            final_msg += f"\n💾 存储：{storage_info['used_gb']}GB / {storage_info['total_gb']}GB ({storage_info['usage_percent']}%)"

        # 合并签到和答题信息
        task_info = signin_msg
        if answer_msg:
            task_info += f"，{answer_msg}"
        final_msg += f"\n📝 签到：{task_info}"

        final_msg += f"\n⏰ 时间：{now_beijing().strftime('%Y-%m-%d %H:%M:%S')}"

        # 签到或答题任一成功都算成功
        is_success = signin_success or answer_success
        logger.info(f"{'任务完成' if is_success else '任务失败'}")
        return final_msg, is_success

def main():
    """主程序入口"""
    logger.info(f"==== 百度网盘签到开始 - {now_beijing().strftime('%Y-%m-%d %H:%M:%S')} ====")

    # 获取Cookie配置
    if not BAIDU_COOKIE:
        error_msg = "未找到BAIDU_COOKIE环境变量，请查看 README.md 配置说明"
        logger.error(error_msg)
        safe_send_notify("[百度网盘]签到失败", error_msg)
        return

    # 支持多账号（用换行分隔）
    if '\n' in BAIDU_COOKIE:
        cookies = [cookie.strip() for cookie in BAIDU_COOKIE.split('\n') if cookie.strip()]
    else:
        cookies = [BAIDU_COOKIE.strip()]

    logger.info(f"共发现 {len(cookies)} 个账号")

    success_count = 0
    total_count = len(cookies)

    for index, cookie in enumerate(cookies):
        try:
            # 账号间随机等待
            if index > 0:
                delay = random.uniform(10, 20)
                logger.info(f"随机等待 {delay:.1f} 秒后处理下一个账号...")
                time.sleep(delay)

            # 执行签到
            baidu_pan = BaiduPan(cookie, index + 1)
            result_msg, is_success = baidu_pan.main()

            if is_success:
                success_count += 1

            # 发送单个账号通知
            status = "成功" if is_success else "失败"
            title = f"[百度网盘]签到{status}"
            safe_send_notify(title, result_msg)

        except Exception as e:
            error_msg = f"账号{index + 1}: 执行异常 - {str(e)}"
            logger.error(error_msg)
            safe_send_notify("[百度网盘]签到失败", error_msg)

    # 发送汇总通知
    if total_count > 1:
        summary_msg = f"""🌐 域名：{BAIDU_DOMAIN.replace('https://', '').replace('http://', '')}

📊 签到汇总：
✅ 成功：{success_count}个
❌ 失败：{total_count - success_count}个
📈 成功率：{success_count/total_count*100:.1f}%
⏰ 完成时间：{now_beijing().strftime('%Y-%m-%d %H:%M:%S')}"""

        safe_send_notify("[百度网盘]签到汇总", summary_msg)

    logger.info(f"==== 百度网盘签到完成 - 成功{success_count}/{total_count} - {now_beijing().strftime('%Y-%m-%d %H:%M:%S')} ====")

def handler(event, context):
    """云函数入口"""
    main()

if __name__ == "__main__":
    main()
