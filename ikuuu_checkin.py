#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
cron: 0 21 * * *
new Env('iKuuu签到')

原始脚本来源: https://github.com/bighammer-link/jichang_dailycheckin
本脚本基于原作者的代码进行了适配和优化，以符合本脚本库的统一标准
感谢原作者的贡献！
"""

import sys
import io

# 设置标准输出编码为UTF-8（解决Windows环境emoji显示问题）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import requests
import json
import re
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
        formatted_msg = f"{timestamp} {level} {message}"
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
IKUUU_EMAIL = os.environ.get('IKUUU_EMAIL', '')
IKUUU_PASSWD = os.environ.get('IKUUU_PASSWD', '')

# ikuuu.de 域名配置
BASE_URL = 'https://ikuuu.de'
LOGIN_URL = f'{BASE_URL}/auth/login'
CHECK_URL = f'{BASE_URL}/user/checkin'

HEADER = {
    'origin': BASE_URL,
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'referer': f'{BASE_URL}/user',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'x-requested-with': 'XMLHttpRequest'
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

class IkuuuSigner:
    name = "iKuuu"

    def __init__(self, email: str, passwd: str, index: int = 1):
        self.email = email
        self.passwd = passwd
        self.index = index
        self.session = requests.Session()
        self.session.headers.update(HEADER)

    def login(self):
        """用户登录"""
        logger.info(f"开始登录...")
        logger.info(f"账号: {self.email}")
        logger.info(f"使用域名: {BASE_URL}")

        try:
            data = {
                'email': self.email,
                'passwd': self.passwd
            }

            response = self.session.post(
                url=LOGIN_URL,
                data=data,
                timeout=15
            )

            logger.debug(f"API 请求：POST {LOGIN_URL} {response.status_code}")
            logger.debug(f"响应：{response.text[:300]}")

            if response.status_code == 200:
                try:
                    result = response.json()

                    if result.get('ret') == 1:
                        logger.info("登录成功")
                        return True, "登录成功"
                    else:
                        error_msg = result.get('msg', '登录失败')
                        logger.error(f"登录失败，原因：{error_msg}")
                        return False, f"登录失败: {error_msg}"

                except json.JSONDecodeError:
                    logger.error(f"登录失败，原因：响应格式错误 - {response.text[:200]}")
                    return False, "登录响应格式错误"
            else:
                error_msg = f"登录请求失败，状态码: {response.status_code}"
                logger.error(f"登录失败，原因：{error_msg}")
                return False, error_msg

        except requests.exceptions.Timeout:
            error_msg = "登录请求超时"
            logger.error(f"登录失败，原因：{error_msg}")
            return False, error_msg
        except requests.exceptions.ConnectionError:
            error_msg = "网络连接错误，请检查域名是否正确"
            logger.error(f"登录失败，原因：{error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"登录异常: {str(e)}"
            logger.error(f"登录失败，原因：{error_msg}")
            return False, error_msg

    def checkin(self):
        """执行签到"""
        logger.info("开始签到...")

        try:
            response = self.session.post(
                url=CHECK_URL,
                timeout=15
            )

            logger.debug(f"API 请求：POST {CHECK_URL} {response.status_code}")
            logger.debug(f"响应：{response.text[:300]}")

            if response.status_code == 200:
                try:
                    result = response.json()

                    msg = result.get('msg', '签到完成')

                    # 从签到响应中提取流量奖励信息
                    traffic_reward = self.extract_traffic_reward(msg, result)

                    # 判断签到结果
                    if result.get('ret') == 1:
                        success_msg = f"签到成功"
                        if traffic_reward:
                            success_msg += f"，获得流量: {traffic_reward}"
                        else:
                            success_msg += f"，{msg}"
                        logger.info(success_msg)
                        return True, success_msg
                    elif "已经签到" in msg or "already" in msg.lower() or result.get('ret') == 0:
                        already_msg = f"今日已签到"
                        if "已经签到" not in msg:
                            already_msg += f": {msg}"
                        logger.info(already_msg)
                        return True, already_msg
                    else:
                        logger.error(f"签到失败，原因：{msg}")
                        return False, f"签到失败: {msg}"

                except json.JSONDecodeError:
                    logger.error(f"签到失败，原因：响应格式错误 - {response.text[:200]}")
                    return False, "签到响应格式错误"
            else:
                error_msg = f"签到请求失败，状态码: {response.status_code}"
                logger.error(f"签到失败，原因：{error_msg}")
                return False, error_msg

        except requests.exceptions.Timeout:
            error_msg = "签到请求超时"
            logger.error(f"签到失败，原因：{error_msg}")
            return False, error_msg
        except requests.exceptions.ConnectionError:
            error_msg = "网络连接错误"
            logger.error(f"签到失败，原因：{error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"签到异常: {str(e)}"
            logger.error(f"签到失败，原因：{error_msg}")
            return False, error_msg

    def extract_traffic_reward(self, msg, result):
        """从签到响应中提取流量奖励信息"""
        logger.debug("开始提取流量奖励信息...")

        try:
            # 常见的流量奖励格式
            traffic_patterns = [
                r'获得[了]?\s*(\d+(?:\.\d+)?)\s*([KMGT]?B)',  # 获得 100MB
                r'奖励[了]?\s*(\d+(?:\.\d+)?)\s*([KMGT]?B)',  # 奖励 100MB
                r'增加[了]?\s*(\d+(?:\.\d+)?)\s*([KMGT]?B)',  # 增加 100MB
                r'签到成功.*?(\d+(?:\.\d+)?)\s*([KMGT]?B)',  # 签到成功，获得100MB
                r'(\d+(?:\.\d+)?)\s*([KMGT]?B).*?流量',     # 100MB 流量
                r'流量.*?(\d+(?:\.\d+)?)\s*([KMGT]?B)',     # 流量 100MB
                r'(\d+(?:\.\d+)?)\s*([KMGT]?B)',           # 直接的数字+单位
            ]

            # 尝试从msg中提取
            for pattern in traffic_patterns:
                match = re.search(pattern, msg, re.I)
                if match:
                    traffic = f"{match.group(1)}{match.group(2)}"
                    logger.debug(f"从消息中提取到流量奖励: {traffic}")
                    return traffic

            # 尝试从result的其他字段中提取
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, str):
                        for pattern in traffic_patterns:
                            match = re.search(pattern, value, re.I)
                            if match:
                                traffic = f"{match.group(1)}{match.group(2)}"
                                logger.debug(f"从{key}字段提取到流量奖励: {traffic}")
                                return traffic

            logger.debug("未提取到流量奖励信息")
            return None

        except Exception as e:
            logger.warning(f"提取流量奖励异常: {e}")
            return None

    def main(self):
        """主执行函数"""
        logger.info(f"\n==== ikuuu账号{self.index} 开始签到 ====")

        if not self.email.strip() or not self.passwd.strip():
            error_msg = "账号配置错误：邮箱或密码为空，请查看 README.md 配置说明"
            logger.error(error_msg)
            return error_msg, False

        # 1. 登录
        login_success, login_msg = self.login()
        if not login_success:
            return f"登录失败: {login_msg}", False

        # 2. 随机等待
        delay = random.uniform(1, 3)
        logger.debug(f"随机等待 {delay:.1f} 秒...")
        time.sleep(delay)

        # 3. 执行签到
        checkin_success, checkin_msg = self.checkin()

        # 4. 组合结果消息（统一模板）
        final_msg = f"""🌐 域名：ikuuu.de

👤 账号{self.index}：
📱 用户：{self.email}
📝 签到：{checkin_msg}
⏰ 时间：{now_beijing().strftime('%Y-%m-%d %H:%M:%S')}"""

        if checkin_success:
            logger.info("任务完成")
        else:
            logger.error("任务失败")

        return final_msg, checkin_success

def main():
    """主程序入口"""
    logger.info(f"==== ikuuu签到开始 - {now_beijing().strftime('%Y-%m-%d %H:%M:%S')} ====")
    logger.info(f"当前域名: {BASE_URL}")

    # 获取账号配置
    emails = IKUUU_EMAIL.split(',') if IKUUU_EMAIL else []
    passwords = IKUUU_PASSWD.split(',') if IKUUU_PASSWD else []

    # 清理空白项
    emails = [email.strip() for email in emails if email.strip()]
    passwords = [passwd.strip() for passwd in passwords if passwd.strip()]

    if not emails or not passwords:
        error_msg = "未找到IKUUU_EMAIL或IKUUU_PASSWD环境变量，请查看 README.md 配置说明"
        logger.error(error_msg)
        safe_send_notify("[iKuuu]签到失败", error_msg)
        return

    if len(emails) != len(passwords):
        error_msg = f"邮箱和密码数量不匹配（邮箱:{len(emails)}，密码:{len(passwords)}），请查看 README.md 配置说明"
        logger.error(error_msg)
        safe_send_notify("[iKuuu]签到失败", error_msg)
        return

    logger.info(f"共发现 {len(emails)} 个账号")

    success_count = 0
    total_count = len(emails)

    for index, (email, passwd) in enumerate(zip(emails, passwords)):
        try:
            # 账号间随机等待
            if index > 0:
                delay = random.uniform(5, 15)
                logger.info(f"随机等待 {delay:.1f} 秒后处理下一个账号...")
                time.sleep(delay)

            # 执行签到
            signer = IkuuuSigner(email, passwd, index + 1)
            result_msg, is_success = signer.main()

            if is_success:
                success_count += 1

            # 发送单个账号通知（统一标题格式）
            status = "成功" if is_success else "失败"
            title = f"[iKuuu]签到{status}"
            safe_send_notify(title, result_msg)

        except Exception as e:
            error_msg = f"账号{index + 1}({email}): 执行异常 - {str(e)}"
            logger.error(error_msg)
            safe_send_notify(f"[iKuuu]账号{index + 1}签到失败", error_msg)

    # 发送汇总通知（统一格式）
    if total_count > 1:
        summary_msg = f"""🌐 域名：ikuuu.de

📊 签到汇总：
✅ 成功：{success_count}个
❌ 失败：{total_count - success_count}个
📈 成功率：{success_count/total_count*100:.1f}%
⏰ 完成时间：{now_beijing().strftime('%Y-%m-%d %H:%M:%S')}"""

        safe_send_notify("[iKuuu]签到汇总", summary_msg)

    logger.info(f"\n==== ikuuu签到完成 - 成功{success_count}/{total_count} - {now_beijing().strftime('%Y-%m-%d %H:%M:%S')} ====")

def handler(event, context):
    """云函数入口"""
    main()

if __name__ == "__main__":
    main()
