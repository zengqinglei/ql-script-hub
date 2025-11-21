#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
cron: 0 21 * * *
new Env('ikuuu签到')

原始脚本来源: https://github.com/bighammer-link/jichang_dailycheckin
本脚本基于原作者的代码进行了适配和优化，以符合本脚本库的统一标准
感谢原作者的贡献！
"""

import os
import requests
import json
import re
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

class IkuuuSigner:
    name = "ikuuu"

    def __init__(self, email: str, passwd: str, index: int = 1):
        self.email = email
        self.passwd = passwd
        self.index = index
        self.session = requests.Session()
        self.session.headers.update(HEADER)

    def login(self):
        """用户登录"""
        try:
            print(f"🔐 正在登录账号: {self.email}")
            print(f"🌐 使用域名: {BASE_URL}")
            
            data = {
                'email': self.email,
                'passwd': self.passwd
            }
            
            response = self.session.post(
                url=LOGIN_URL, 
                data=data, 
                timeout=15
            )
            
            print(f"🔍 登录响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"🔍 登录响应: {result}")
                    
                    if result.get('ret') == 1:
                        print(f"✅ 登录成功: {result.get('msg', '登录成功')}")
                        return True, "登录成功"
                    else:
                        error_msg = result.get('msg', '登录失败')
                        print(f"❌ 登录失败: {error_msg}")
                        return False, f"登录失败: {error_msg}"
                        
                except json.JSONDecodeError:
                    print(f"❌ 登录响应格式错误: {response.text[:200]}")
                    return False, "登录响应格式错误"
            else:
                error_msg = f"登录请求失败，状态码: {response.status_code}"
                print(f"❌ {error_msg}")
                return False, error_msg
                
        except requests.exceptions.Timeout:
            error_msg = "登录请求超时"
            print(f"❌ {error_msg}")
            return False, error_msg
        except requests.exceptions.ConnectionError:
            error_msg = "网络连接错误，请检查域名是否正确"
            print(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"登录异常: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg

    def checkin(self):
        """执行签到"""
        try:
            print("📝 正在执行签到...")
            
            response = self.session.post(
                url=CHECK_URL, 
                timeout=15
            )
            
            print(f"🔍 签到响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"🔍 签到响应: {result}")
                    
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
                        print(f"✅ {success_msg}")
                        return True, success_msg
                    elif "已经签到" in msg or "already" in msg.lower() or result.get('ret') == 0:
                        already_msg = f"今日已签到"
                        if "已经签到" not in msg:
                            already_msg += f": {msg}"
                        print(f"📅 {already_msg}")
                        return True, already_msg
                    else:
                        print(f"❌ 签到失败: {msg}")
                        return False, f"签到失败: {msg}"
                        
                except json.JSONDecodeError:
                    print(f"❌ 签到响应格式错误: {response.text[:200]}")
                    return False, "签到响应格式错误"
            else:
                error_msg = f"签到请求失败，状态码: {response.status_code}"
                print(f"❌ {error_msg}")
                return False, error_msg
                
        except requests.exceptions.Timeout:
            error_msg = "签到请求超时"
            print(f"❌ {error_msg}")
            return False, error_msg
        except requests.exceptions.ConnectionError:
            error_msg = "网络连接错误"
            print(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"签到异常: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg

    def extract_traffic_reward(self, msg, result):
        """从签到响应中提取流量奖励信息"""
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
                    print(f"🎁 从消息中提取到流量奖励: {traffic}")
                    return traffic
            
            # 尝试从result的其他字段中提取
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, str):
                        for pattern in traffic_patterns:
                            match = re.search(pattern, value, re.I)
                            if match:
                                traffic = f"{match.group(1)}{match.group(2)}"
                                print(f"🎁 从{key}字段提取到流量奖励: {traffic}")
                                return traffic
            
            return None
            
        except Exception as e:
            print(f"⚠️ 提取流量奖励异常: {e}")
            return None

    def main(self):
        """主执行函数"""
        print(f"\n==== ikuuu账号{self.index} 开始签到 ====")
        
        if not self.email.strip() or not self.passwd.strip():
            error_msg = "❌ 账号配置错误：邮箱或密码为空，请查看 README.md 配置说明"
            print(f"❌ {error_msg}")
            return error_msg, False

        # 1. 登录
        login_success, login_msg = self.login()
        if not login_success:
            return f"登录失败: {login_msg}", False
        
        # 2. 随机等待
        time.sleep(random.uniform(1, 3))
        
        # 3. 执行签到
        checkin_success, checkin_msg = self.checkin()
        
        # 4. 组合结果消息（统一模板）
        final_msg = f"""🌐 域名：ikuuu.de

👤 账号{self.index}：
📱 用户：{self.email}
📝 签到：{checkin_msg}
⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        print(f"{'✅ 任务完成' if checkin_success else '❌ 任务失败'}")
        return final_msg, checkin_success

def main():
    """主程序入口"""
    print(f"==== ikuuu签到开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====")
    print(f"🌐 当前域名: {BASE_URL}")

    # 获取账号配置
    emails = IKUUU_EMAIL.split(',') if IKUUU_EMAIL else []
    passwords = IKUUU_PASSWD.split(',') if IKUUU_PASSWD else []
    
    # 清理空白项
    emails = [email.strip() for email in emails if email.strip()]
    passwords = [passwd.strip() for passwd in passwords if passwd.strip()]
    
    if not emails or not passwords:
        error_msg = "❌ 未找到IKUUU_EMAIL或IKUUU_PASSWD环境变量，请查看 README.md 配置说明"
        print(error_msg)
        notify_user("ikuuu签到失败", error_msg)
        return

    if len(emails) != len(passwords):
        error_msg = f"❌ 邮箱和密码数量不匹配（邮箱:{len(emails)}，密码:{len(passwords)}），请查看 README.md 配置说明"
        print(error_msg)
        notify_user("ikuuu签到失败", error_msg)
        return
    
    print(f"📝 共发现 {len(emails)} 个账号")
    
    success_count = 0
    total_count = len(emails)

    for index, (email, passwd) in enumerate(zip(emails, passwords)):
        try:
            # 账号间随机等待
            if index > 0:
                delay = random.uniform(5, 15)
                print(f"⏱️  随机等待 {delay:.1f} 秒后处理下一个账号...")
                time.sleep(delay)

            # 执行签到
            signer = IkuuuSigner(email, passwd, index + 1)
            result_msg, is_success = signer.main()

            if is_success:
                success_count += 1

            # 发送单个账号通知（统一标题格式）
            status = "成功" if is_success else "失败"
            title = f"[ikuuu]签到{status}"
            notify_user(title, result_msg)
            
        except Exception as e:
            error_msg = f"账号{index + 1}({email}): 执行异常 - {str(e)}"
            print(f"❌ {error_msg}")
            notify_user(f"ikuuu账号{index + 1}签到失败", error_msg)
    
    # 发送汇总通知（统一格式）
    if total_count > 1:
        summary_msg = f"""🌐 域名：ikuuu.de

📊 签到汇总：
✅ 成功：{success_count}个
❌ 失败：{total_count - success_count}个
📈 成功率：{success_count/total_count*100:.1f}%
⏰ 完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        notify_user("[ikuuu]签到汇总", summary_msg)
    
    print(f"\n==== ikuuu签到完成 - 成功{success_count}/{total_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====")

def handler(event, context):
    """云函数入口"""
    main()

if __name__ == "__main__":
    main()
