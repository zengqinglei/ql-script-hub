#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cron "0 9 * * *" script-path=agentrouter_checkin.py,tag=AgentRouter签到
new Env('AgentRouter签到')

AgentRouter 自动签到青龙脚本
适用于青龙面板定时任务执行
"""

import json
import os
import random
import re
import sys
import time
from datetime import datetime, timedelta

import requests

# 导入 execjs（用于执行 WAF JavaScript）
try:
    import execjs
    HAS_EXECJS = True
except ImportError:
    HAS_EXECJS = False
    print("⚠️  未安装 PyExecJS，WAF 挑战可能失败")
    print("   安装方法：pip install PyExecJS")


# ---------------- 可选通知模块 ----------------
hadsend = False
notify_error = None
try:
    from notify import send
    hadsend = True
    print("✅ 通知模块加载成功")
except Exception as e:
    notify_error = str(e)
    print(f"⚠️ 通知模块加载失败: {e}")
    def send(title, content):
        pass


# ---------------- 配置项 ----------------
TIMEOUT = int(os.getenv("AGENTROUTER_TIMEOUT", "30"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
VERIFY_SSL = os.getenv("AGENTROUTER_VERIFY_SSL", "true").lower() == "true"
MAX_RETRIES = int(os.getenv("AGENTROUTER_MAX_RETRIES", "3"))
BASE_URL = os.getenv("AGENTROUTER_BASE_URL", "https://agentrouter.org")  # 支持自定义域名

# 随机延迟配置
max_random_delay = int(os.getenv("MAX_RANDOM_DELAY", "3600"))
random_signin = os.getenv("RANDOM_SIGNIN", "true").lower() == "true"


def format_time_remaining(seconds):
    """格式化时间显示"""
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


def wait_with_countdown(delay_seconds):
    """带倒计时的等待"""
    if delay_seconds <= 0:
        return

    print(f"AgentRouter签到需要等待 {format_time_remaining(delay_seconds)}")

    remaining = delay_seconds
    while remaining > 0:
        if remaining <= 10 or remaining % 10 == 0:
            print(f"倒计时: {format_time_remaining(remaining)}")

        sleep_time = 1 if remaining <= 10 else min(10, remaining)
        time.sleep(sleep_time)
        remaining -= sleep_time


def safe_send_notify(title, content):
    """安全的通知发送（带日志）"""
    if not hadsend:
        print(f"📢 [通知] {title}: {content}")
        print("   (通知模块未加载，仅控制台显示)")
        return False

    try:
        print(f"📤 正在推送通知: {title}")
        send(title, content)
        print("✅ 通知推送成功")
        return True
    except Exception as e:
        print(f"❌ 通知推送失败: {e}")
        return False


def load_accounts():
    """从环境变量加载多账号配置"""
    accounts_str = os.getenv('AGENTROUTER_ACCOUNTS')
    if not accounts_str:
        print('❌ 未设置 AGENTROUTER_ACCOUNTS 环境变量')
        return None

    try:
        accounts_data = json.loads(accounts_str)

        # 检查是否为数组格式
        if not isinstance(accounts_data, list):
            print('❌ 账号配置必须使用数组格式 [{}]')
            return None

        # 验证账号数据格式
        for i, account in enumerate(accounts_data):
            if not isinstance(account, dict):
                print(f'❌ 账号 {i + 1} 配置格式不正确')
                return None
            if 'cookies' not in account or 'api_user' not in account:
                print(f'❌ 账号 {i + 1} 缺少必需字段 (cookies, api_user)')
                return None

        return accounts_data
    except Exception as e:
        print(f'❌ 账号配置格式不正确: {e}')
        return None


def parse_cookies(cookies_data):
    """解析 cookies 数据"""
    if isinstance(cookies_data, dict):
        return cookies_data

    if isinstance(cookies_data, str):
        cookies_dict = {}
        for cookie in cookies_data.split(';'):
            if '=' in cookie:
                key, value = cookie.strip().split('=', 1)
                cookies_dict[key] = value
        return cookies_dict
    return {}


def build_session(cookies_dict, api_user):
    """构建请求会话"""
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    session = requests.Session()

    # 配置重试策略
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "POST", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # 设置 SSL 验证
    session.verify = VERIFY_SSL
    if not VERIFY_SSL:
        # 禁用 SSL 警告
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # 设置基本headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': f'{BASE_URL}/console',
        'Origin': BASE_URL,
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'New-Api-User': api_user,
    })

    # 设置cookies
    for name, value in cookies_dict.items():
        session.cookies.set(name, value)

    return session


def get_user_info(session):
    """获取用户信息"""
    try:
        response = session.get(f'{BASE_URL}/api/user/self', timeout=TIMEOUT)

        if DEBUG_MODE:
            print(f'  [DEBUG] 用户信息响应状态码: {response.status_code}')
            print(f'  [DEBUG] 用户信息响应内容: {response.text}')

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                user_data = data.get('data', {})
                quota = round(user_data.get('quota', 0) / 500000, 2)
                used_quota = round(user_data.get('used_quota', 0) / 500000, 2)

                if DEBUG_MODE:
                    print(f'  [DEBUG] 解析余额 - quota: {user_data.get("quota", 0)} -> ${quota}')
                    print(f'  [DEBUG] 解析已用 - used_quota: {user_data.get("used_quota", 0)} -> ${used_quota}')

                return True, f'当前余额: ${quota}, 已使用: ${used_quota}'
            else:
                if DEBUG_MODE:
                    print(f'  [DEBUG] 用户信息API返回success=false')
        else:
            if DEBUG_MODE:
                print(f'  [DEBUG] 用户信息请求失败，状态码: {response.status_code}')

        return False, None
    except Exception as e:
        if DEBUG_MODE:
            print(f'  [DEBUG] 获取用户信息异常: {str(e)}')
        return False, None


def get_basic_waf_cookies(session):
    """获取基础 WAF cookies（通过访问登录页）"""
    try:
        if DEBUG_MODE:
            print(f"  🔐 访问登录页获取基础 WAF cookies...")

        # 访问登录页面获取基础 WAF cookies（acw_tc, cdn_sec_tc）
        response = session.get(f'{BASE_URL}/login', timeout=TIMEOUT, allow_redirects=True)

        if DEBUG_MODE:
            print(f'  [DEBUG] 登录页状态码: {response.status_code}')
            print(f'  [DEBUG] 当前 cookies: {list(session.cookies.keys())}')

        # 等待一下让 cookies 生效
        time.sleep(1)

        return True

    except Exception as e:
        if DEBUG_MODE:
            print(f'  [DEBUG] 获取基础 WAF cookies 失败: {str(e)[:50]}')
        return False


def execute_waf_challenge(session, challenge_html, url):
    """执行 WAF JavaScript 挑战"""
    if not HAS_EXECJS:
        print(f"  ❌ 未安装 PyExecJS，无法处理 WAF 挑战")
        return False

    try:
        print(f"  🔒 检测到 WAF 挑战，尝试解决...")

        # 提取 JavaScript 代码
        js_match = re.search(r'<script>(.*?)</script>', challenge_html, re.DOTALL)
        if not js_match:
            if DEBUG_MODE:
                print(f'  [DEBUG] 未找到 JavaScript 挑战代码')
            return False

        js_code = js_match.group(1)

        if DEBUG_MODE:
            print(f'  [DEBUG] WAF JavaScript 长度: {len(js_code)}')

        # 从 BASE_URL 提取 host 和 pathname
        from urllib.parse import urlparse
        parsed_base = urlparse(BASE_URL)
        base_host = parsed_base.netloc
        parsed_url = urlparse(url)
        url_pathname = parsed_url.path

        # 构建完整的浏览器环境模拟，并用 try-catch 包裹 WAF 代码
        js_env = f"""
        // 模拟 document 对象
        var document = {{
            cookie: '',
            set cookie(val) {{
                this._cookie = val;
            }},
            get cookie() {{
                return this._cookie || '';
            }},
            getElementById: function() {{ return null; }},
            getElementsByTagName: function() {{ return []; }},
            createElement: function() {{ return {{}}; }},
            body: {{}},
            head: {{}}
        }};

        // 模拟 location 对象（包含所有可能的属性和方法）
        var location = {{
            href: '{url}',
            protocol: '{parsed_url.scheme}:',
            host: '{base_host}',
            hostname: '{base_host}',
            port: '',
            pathname: '{url_pathname}',
            search: '',
            hash: '',
            origin: '{BASE_URL}',
            reload: function() {{}},
            replace: function() {{}},
            assign: function() {{}},
            toString: function() {{ return this.href; }}
        }};

        // 模拟 navigator 对象
        var navigator = {{
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            platform: 'Win32',
            language: 'zh-CN',
            languages: ['zh-CN', 'zh', 'en'],
            onLine: true,
            cookieEnabled: true
        }};

        // 模拟 window 对象
        var window = this;
        window.location = location;
        window.document = document;
        window.navigator = navigator;
        window.setTimeout = function(fn, delay) {{ if (typeof fn === 'function') try {{ fn(); }} catch(e) {{}} }};
        window.setInterval = function() {{}};
        window.clearTimeout = function() {{}};
        window.clearInterval = function() {{}};
        window.addEventListener = function() {{}};
        window.removeEventListener = function() {{}};

        // 用 try-catch 包裹 WAF JavaScript，忽略执行错误
        try {{
            {js_code}
        }} catch(e) {{
            // 忽略执行错误，只要 cookie 被设置就行
        }}

        // 返回设置的 cookie
        document.cookie;
        """

        # 执行 JavaScript
        ctx = execjs.compile(js_env)
        result = ctx.eval('document.cookie')

        if DEBUG_MODE:
            print(f'  [DEBUG] JavaScript 执行结果: {result[:100] if result else "None"}...')

        # 解析 cookie
        if result and 'acw_sc__v2=' in result:
            # 提取 acw_sc__v2 的值
            cookie_match = re.search(r'acw_sc__v2=([^;]+)', result)
            if cookie_match:
                acw_sc_v2 = cookie_match.group(1)
                session.cookies.set('acw_sc__v2', acw_sc_v2)
                print(f'  ✅ WAF 挑战已解决')
                if DEBUG_MODE:
                    print(f'  [DEBUG] 设置 acw_sc__v2: {acw_sc_v2[:20]}...')
                return True

        if DEBUG_MODE:
            print(f'  [DEBUG] 未能从 JavaScript 结果中提取 acw_sc__v2')
        return False

    except Exception as e:
        print(f'  ❌ 执行 WAF 挑战失败: {str(e)[:100]}')
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
        return False


def check_in_account(account_info, account_index):
    """为单个账号执行签到操作"""
    account_name = f'账号{account_index + 1}'
    print(f"\n==== {account_name} 开始签到 ====")
    print(f"当前时间: {datetime.now().strftime('%H:%M:%S')}")

    # 解析账号配置
    cookies_data = account_info.get('cookies', {})
    api_user = account_info.get('api_user', '')

    if not api_user:
        print(f'{account_name}: ❌ 未找到 API 用户标识')
        return "error", "未找到 API 用户标识", None, None

    # 解析用户 cookies
    user_cookies = parse_cookies(cookies_data)
    if not user_cookies:
        print(f'{account_name}: ❌ 配置格式无效')
        return "error", "配置格式无效", None, None

    # 构建会话
    session = build_session(user_cookies, api_user)

    try:
        # 步骤1：获取基础 WAF cookies
        get_basic_waf_cookies(session)

        # 步骤2：获取签到前的用户信息
        print(f"  📊 获取签到前余额...")
        before_success, before_info = get_user_info(session)
        before_quota = 0
        before_used = 0

        if before_success and before_info:
            print(f"  💰 签到前: {before_info}")
            # 解析余额数据
            quota_match = re.search(r'\$(\d+\.?\d*)', before_info.split(',')[0])
            used_match = re.search(r'\$(\d+\.?\d*)', before_info.split(',')[1])
            if quota_match:
                before_quota = float(quota_match.group(1))
            if used_match:
                before_used = float(used_match.group(1))

        # 步骤3：执行签到
        print(f"  🎯 执行签到...")
        checkin_headers = {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
        session.headers.update(checkin_headers)

        checkin_url = f'{BASE_URL}/api/user/sign_in'
        response = session.post(checkin_url, timeout=TIMEOUT)

        if DEBUG_MODE:
            print(f'  [DEBUG] 签到响应状态码: {response.status_code}')
            print(f'  [DEBUG] 签到响应内容: {response.text}')

        # 检查是否遇到 WAF 挑战
        if response.status_code == 200 and '<script>' in response.text and 'arg1=' in response.text:
            if execute_waf_challenge(session, response.text, checkin_url):
                time.sleep(1)
                response = session.post(checkin_url, timeout=TIMEOUT)
                if DEBUG_MODE:
                    print(f'  [DEBUG] 重试签到响应状态码: {response.status_code}')
                    print(f'  [DEBUG] 重试签到响应内容: {response.text}')
            else:
                return "fail", "WAF 挑战失败", None, None

        if response.status_code == 200:
            try:
                result = response.json()

                if DEBUG_MODE:
                    print(f'  [DEBUG] 签到响应JSON: {json.dumps(result, ensure_ascii=False, indent=2)}')

                if result.get('ret') == 1 or result.get('code') == 0 or result.get('success'):
                    msg = result.get('msg', result.get('message', '签到成功'))

                    # 步骤4：获取签到后的用户信息（计算余额变化）
                    print(f"  📊 获取签到后余额...")
                    time.sleep(1)
                    after_success, after_info = get_user_info(session)
                    after_quota = 0
                    after_used = 0
                    reward_amount = 0

                    if after_success and after_info:
                        print(f"  💰 签到后: {after_info}")
                        # 解析余额数据
                        quota_match = re.search(r'\$(\d+\.?\d*)', after_info.split(',')[0])
                        used_match = re.search(r'\$(\d+\.?\d*)', after_info.split(',')[1])
                        if quota_match:
                            after_quota = float(quota_match.group(1))
                        if used_match:
                            after_used = float(used_match.group(1))

                        # 计算奖励金额（总余额的增加）
                        if before_success:
                            reward_amount = (after_quota + after_used) - (before_quota + before_used)
                            if reward_amount > 0:
                                print(f"  🎁 签到奖励: ${reward_amount:.2f}")
                                msg = f"{msg}，获得 ${reward_amount:.2f}"

                        return "success", msg, after_info, reward_amount
                    else:
                        # 签到成功但获取余额失败
                        return "success", msg, before_info if before_success else None, 0
                else:
                    error_msg = result.get('msg', result.get('message', '未知错误'))
                    return "fail", error_msg, before_info if before_success else None, 0
            except json.JSONDecodeError:
                if 'success' in response.text.lower():
                    return "success", "签到成功", before_info if before_success else None, 0
                else:
                    if DEBUG_MODE:
                        print(f'  [DEBUG] 无法解析响应为 JSON')
                    return "fail", "响应格式无效", before_info if before_success else None, 0

        elif response.status_code == 404:
            # 404保活逻辑：签到接口不存在，尝试查询用户信息进行保活
            print(f"🔍 签到接口返回404，尝试查询用户信息进行保活...")
            try:
                # 使用用户信息接口进行保活
                user_info_url = f'{BASE_URL}/api/user/self'
                user_resp = session.get(user_info_url, timeout=TIMEOUT)

                if user_resp.status_code == 200:
                    user_data = user_resp.json()
                    if user_data.get('success'):
                        print(f"✅ 用户信息查询成功，账号已保活")

                        # 获取用户余额信息用于通知
                        quota = round(user_data.get('data', {}).get('quota', 0) / 500000, 2)
                        used_quota = round(user_data.get('data', {}).get('used_quota', 0) / 500000, 2)
                        user_info = f'当前余额: ${quota}, 已使用: ${used_quota}'

                        return "success", "签到接口不存在，但账号状态正常", user_info, 0
                    else:
                        print(f"⚠️ 用户信息查询失败: {user_data.get('message', 'Unknown error')}")
                        return "fail", f"签到接口404，用户信息查询失败", before_info if before_success else None, 0
                else:
                    print(f"⚠️ 用户信息接口返回 {user_resp.status_code}")
                    return "fail", f"签到接口404，用户信息接口返回{user_resp.status_code}", before_info if before_success else None, 0

            except Exception as e:
                print(f"⚠️ 用户信息查询异常: {e}")
                return "fail", "签到接口404，用户信息查询也失败", before_info if before_success else None, 0

        else:
            return "fail", f"HTTP {response.status_code}", before_info if before_success else None, 0

    except requests.exceptions.Timeout:
        return "error", f"请求超时（{TIMEOUT}秒）", None, 0
    except requests.exceptions.ConnectionError as e:
        return "error", f"连接失败: {str(e)[:80]}", None, 0
    except Exception as e:
        error_msg = f"{e.__class__.__name__}: {str(e)[:100]}"
        print(f'{account_name}: ❌ 签到过程中出错 - {error_msg}')
        return "error", error_msg, None, 0
    finally:
        session.close()


def main():
    """主函数"""
    print(f"{'='*50}")
    print(f"  AgentRouter 签到脚本 v1.0")
    print(f"  执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if DEBUG_MODE:
        print(f"  🐛 调试模式: 已启用")
    print(f"{'='*50}\n")

    # 随机延迟（可选）
    if random_signin:
        delay_seconds = random.randint(0, max_random_delay)
        if delay_seconds > 0:
            signin_time = datetime.now() + timedelta(seconds=delay_seconds)
            print(f"随机模式: 延迟 {format_time_remaining(delay_seconds)} 后签到")
            print(f"预计签到时间: {signin_time.strftime('%H:%M:%S')}\n")
            wait_with_countdown(delay_seconds)

    # 加载账号配置
    accounts = load_accounts()
    if not accounts:
        print('❌ 无法加载账号配置，程序退出')
        sys.exit(1)

    print(f"共发现 {len(accounts)} 个账号配置\n")
    print("==== 开始执行签到任务 ====\n")

    # 为每个账号执行签到
    success_count = 0
    fail_count = 0
    error_count = 0

    for i, account in enumerate(accounts):
        name = f"账号{i + 1}"

        try:
            status, msg, user_info, reward = check_in_account(account, i)

            if status == "success":
                success_count += 1
                print(f"✅ {name} 签到成功: {msg}")
                if user_info:
                    print(f"💰 {user_info}")

                # 统一通知格式
                notify_content = f"""🌐 域名：{BASE_URL.replace('https://', '').replace('http://', '')}

👤 {name}：
📝 签到：{msg}"""

                if user_info:
                    notify_content += f"\n💰 账户：{user_info}"

                notify_content += f"\n⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                safe_send_notify("[AgentRouter]签到成功", notify_content)

            elif status == "fail":
                fail_count += 1
                print(f"⚠️ {name} 签到失败: {msg}")
                if user_info:
                    print(f"💰 {user_info}")

                # 统一通��格式
                notify_content = f"""🌐 域名：{BASE_URL.replace('https://', '').replace('http://', '')}

👤 {name}：
📝 签到：{msg}"""

                if user_info:
                    notify_content += f"\n💰 账户：{user_info}"

                notify_content += f"\n⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                safe_send_notify("[AgentRouter]签到失败", notify_content)

            else:  # error
                error_count += 1
                print(f"❌ {name} 签到出错: {msg}")

                # 统一通知格式
                notify_content = f"""🌐 域名：{BASE_URL.replace('https://', '').replace('http://', '')}

👤 {name}：
📝 签到：签到出错 - {msg}
⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

                safe_send_notify("[AgentRouter]签到出错", notify_content)

        except Exception as e:
            error_count += 1
            error_msg = f"{e.__class__.__name__}: {str(e)[:50]}"
            print(f"❌ {name} 处理异常: {error_msg}")

            # 统一通知格式
            notify_content = f"""🌐 域名：{BASE_URL.replace('https://', '').replace('http://', '')}

👤 {name}：
📝 签到：签到异常 - {error_msg}
⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

            safe_send_notify("[AgentRouter]签到异常", notify_content)

        # 账号间延迟
        if i < len(accounts) - 1:
            time.sleep(3)

    print(f"\n{'='*50}")
    print(f"  所有账号签到完成")
    print(f"  ✅ 成功: {success_count} | ⚠️ 失败: {fail_count} | ❌ 出错: {error_count}")
    print(f"  完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    # 发送汇总通知（仅多账号时，统一格式）
    if len(accounts) > 1:
        summary = f"""🌐 域名：{BASE_URL.replace('https://', '').replace('http://', '')}

📊 签到汇总：
✅ 成功：{success_count}个
⚠️ 失败：{fail_count}个
❌ 出错：{error_count}个
📈 成功率：{success_count/len(accounts)*100:.1f}%
⏰ 完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        safe_send_notify("[AgentRouter]签到汇总", summary)

    # 设置退出码
    sys.exit(0 if success_count > 0 else 1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n⚠️ 程序被用户中断')
        sys.exit(1)
    except Exception as e:
        print(f'❌ 程序执行过程中发生错误: {e}')
        sys.exit(1)