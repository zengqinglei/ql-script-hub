#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
cron: 15 10 * * *
new Env('z.luxury签到')

z.luxury 自动签到脚本
支持对接 YesCaptcha 打码平台进行 Recaptcha v2 验证

配置说明：
1. 环境变量 Z_LUXURY_EMAIL: 登录账号 (必需)
2. 环境变量 Z_LUXURY_PASSWD: 登录密码 (必需)
3. 环境变量 YESCAPTCHA_CLIENT_KEY: YesCaptcha 的 Client Key (必需，用于过验证码)
   - 注册地址: https://yescaptcha.com/
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
Z_LUXURY_EMAIL = os.environ.get('Z_LUXURY_EMAIL', '')
Z_LUXURY_PASSWD = os.environ.get('Z_LUXURY_PASSWD', '')
YESCAPTCHA_CLIENT_KEY = os.environ.get('YESCAPTCHA_CLIENT_KEY', '')
Z_LUXURY_DOMAIN = os.environ.get('Z_LUXURY_DOMAIN', 'https://z.luxury')

# 域名配置
BASE_URL = Z_LUXURY_DOMAIN
LOGIN_URL = f'{BASE_URL}/signin'
CHECK_URL = f'{BASE_URL}/user/checkin'
USER_INFO_URL = f'{BASE_URL}/xiaoma/user'
SITE_KEY = "6LdvLZohAAAAANKRXPlQm0A8DqxNUHbtiXme8N_Y"  # 网站的 Recaptcha SiteKey

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

class ZLuxurySigner:
    name = "z.luxury"

    def __init__(self, email: str, passwd: str, captcha_key: str, index: int = 1):
        self.email = email
        self.passwd = passwd
        self.captcha_key = captcha_key
        self.index = index
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': f'{BASE_URL}/user',
            'Origin': BASE_URL,
            'Accept': 'application/json, text/plain, */*',
        })

    def login(self):
        """用户登录"""
        logger.info(f"开始登录...")
        logger.info(f"账号: {self.email}")
        
        try:
            data = {
                'email': self.email,
                'passwd': self.passwd
            }

            response = self.session.post(
                url=LOGIN_URL,
                json=data,
                timeout=30
            )

            logger.debug(f"API 请求：POST {LOGIN_URL} {response.status_code}")
            logger.debug(f"响应：{response.text[:300]}")

            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('code') == 200:
                        logger.info("登录成功")
                        return True, "登录成功"
                    else:
                        error_msg = result.get('msg', '登录失败')
                        logger.error(f"登录失败，原因：{error_msg}")
                        return False, f"登录失败: {error_msg}"
                except json.JSONDecodeError:
                    logger.error("登录响应格式错误")
                    return False, "登录响应格式错误"
            else:
                error_msg = f"登录请求失败，状态码: {response.status_code}"
                logger.error(error_msg)
                return False, error_msg

        except Exception as e:
            error_msg = f"登录异常: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def check_status(self):
        """检查签到状态"""
        logger.info("正在检查签到状态...")
        try:
            response = self.session.get(USER_INFO_URL, timeout=30)
            logger.debug(f"API 请求：GET {USER_INFO_URL} {response.status_code}")
            
            try:
                result = response.json()
                if result.get("code") == 200:
                    data = result.get("data", {})
                    is_checked = data.get("check_in", False)
                    user_shop = data.get("user_shop", "未知")
                    
                    logger.info(f"用户组: {user_shop}")
                    logger.info(f"今日已签到: {is_checked}")
                    return is_checked, user_shop
                else:
                    logger.error(f"获取用户信息失败: {result}")
                    return None, "未知"
            except json.JSONDecodeError:
                logger.error("用户信息响应解析失败")
                return None, "未知"
                
        except Exception as e:
            logger.error(f"检查状态异常: {e}")
            return None, "未知"

    def solve_captcha(self):
        """使用 YesCaptcha 识别验证码"""
        if not self.captcha_key:
            logger.error("未配置 YESCAPTCHA_CLIENT_KEY，无法进行验证码识别")
            return None

        logger.info("正在请求 YesCaptcha 创建验证码任务...")
        
        create_task_url = "https://api.yescaptcha.com/createTask"
        data = {
            "clientKey": self.captcha_key,
            "task": {
                "type": "RecaptchaV2TaskProxyless",
                "websiteURL": f"{BASE_URL}/user",
                "websiteKey": SITE_KEY
            }
        }

        try:
            # 创建任务
            response = requests.post(create_task_url, json=data, timeout=30)
            result = response.json()
            
            if result.get("errorId") != 0:
                logger.error(f"创建验证码任务失败: {result}")
                return None
                
            task_id = result.get("taskId")
            logger.info(f"验证码任务创建成功，ID: {task_id}，正在等待结果...")
            
            # 轮询结果
            for _ in range(60):
                time.sleep(2)
                get_result_url = "https://api.yescaptcha.com/getTaskResult"
                result_data = {
                    "clientKey": self.captcha_key,
                    "taskId": task_id
                }
                
                res = requests.post(get_result_url, json=result_data, timeout=30)
                res_json = res.json()
                
                if res_json.get("status") == "ready":
                    token = res_json.get("solution", {}).get("gRecaptchaResponse")
                    logger.info("验证码识别成功！")
                    return token
                
                if res_json.get("status") == "processing":
                    continue
                    
                logger.error(f"获取验证码结果失败: {res_json}")
                return None
                
            logger.error("验证码识别超时")
            return None

        except Exception as e:
            logger.error(f"验证码识别异常: {e}")
            return None

    def checkin(self):
        """执行签到"""
        # 1. 检查状态
        is_checked, user_shop = self.check_status()
        if is_checked:
            logger.info("今日已签到，无需重复签到")
            return True, "今日已签到"
        elif is_checked is None:
            return False, "状态获取失败"

        # 2. 识别验证码
        recaptcha_token = self.solve_captcha()
        if not recaptcha_token:
            return False, "验证码识别失败"

        # 3. 提交签到
        logger.info("正在提交签到请求...")
        
        try:
            data = {
                "recaptcha": recaptcha_token
            }
            response = self.session.post(CHECK_URL, json=data, timeout=30)
            logger.debug(f"API 请求：POST {CHECK_URL} {response.status_code}")
            logger.debug(f"响应：{response.text[:300]}")
            
            try:
                result = response.json()
                msg = result.get('msg', '签到完成')
                
                if result.get("ret") == 1 or result.get("code") == 200:
                    logger.info(f"签到成功: {msg}")
                    return True, f"签到成功: {msg}"
                else:
                    logger.error(f"签到失败: {msg}")
                    return False, f"签到失败: {msg}"
            except json.JSONDecodeError:
                logger.error("签到响应解析失败")
                return False, "签到响应解析失败"
                
        except Exception as e:
            error_msg = f"签到请求异常: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def main(self):
        """主执行函数"""
        logger.info(f"\n==== 账号{self.index} 开始签到 ====")

        if not self.email or not self.passwd:
            error_msg = "账号配置错误：邮箱或密码为空"
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

        # 4. 获取最新状态
        _, user_shop = self.check_status()

        # 5. 组合结果消息
        final_msg = f"""🌐 域名：{BASE_URL}

👤 账号{self.index}：
📱 用户：{self.email}
🔰 用户组：{user_shop}
📝 签到：{checkin_msg}
⏰ 时间：{now_beijing().strftime('%Y-%m-%d %H:%M:%S')}"""

        if checkin_success:
            logger.info("任务完成")
        else:
            logger.error("任务失败")

        return final_msg, checkin_success

def main():
    """主程序入口"""
    logger.info(f"==== z.luxury签到开始 - {now_beijing().strftime('%Y-%m-%d %H:%M:%S')} ====")
    logger.info(f"当前域名: {BASE_URL}")

    if not YESCAPTCHA_CLIENT_KEY:
        logger.warning("未配置 YESCAPTCHA_CLIENT_KEY，可能无法通过人机验证")

    # 获取账号配置
    emails = Z_LUXURY_EMAIL.split(',') if Z_LUXURY_EMAIL else []
    passwords = Z_LUXURY_PASSWD.split(',') if Z_LUXURY_PASSWD else []

    # 清理空白项
    emails = [email.strip() for email in emails if email.strip()]
    passwords = [passwd.strip() for passwd in passwords if passwd.strip()]

    if not emails or not passwords:
        error_msg = "未找到 Z_LUXURY_EMAIL 或 Z_LUXURY_PASSWD 环境变量"
        logger.error(error_msg)
        safe_send_notify("[z.luxury]签到失败", error_msg)
        return

    if len(emails) != len(passwords):
        error_msg = f"邮箱和密码数量不匹配（邮箱:{len(emails)}，密码:{len(passwords)}）"
        logger.error(error_msg)
        safe_send_notify("[z.luxury]签到失败", error_msg)
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
            signer = ZLuxurySigner(email, passwd, YESCAPTCHA_CLIENT_KEY, index + 1)
            result_msg, is_success = signer.main()

            if is_success:
                success_count += 1

            # 发送单个账号通知
            status = "成功" if is_success else "失败"
            title = f"[z.luxury]签到{status}"
            safe_send_notify(title, result_msg)

        except Exception as e:
            error_msg = f"账号{index + 1}({email}): 执行异常 - {str(e)}"
            logger.error(error_msg)
            safe_send_notify(f"[z.luxury]账号{index + 1}签到失败", error_msg)

    # 发送汇总通知
    if total_count > 1:
        summary_msg = f"""🌐 域名：{BASE_URL}

📊 签到汇总：
✅ 成功：{success_count}个
❌ 失败：{total_count - success_count}个
📈 成功率：{success_count/total_count*100:.1f}%
⏰ 完成时间：{now_beijing().strftime('%Y-%m-%d %H:%M:%S')}"""

        safe_send_notify("[z.luxury]签到汇总", summary_msg)

    logger.info(f"\n==== z.luxury签到完成 - 成功{success_count}/{total_count} - {now_beijing().strftime('%Y-%m-%d %H:%M:%S')} ====")

def handler(event, context):
    """云函数入口"""
    main()

if __name__ == "__main__":
    main()