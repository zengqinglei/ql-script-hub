#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cron "0 9 * * *" script-path=anyrouter_checkin.py,tag=AnyRouter签到
new Env('AnyRouter签到')

AnyRouter.top 自动签到青龙脚本
适用于青龙面板定时任务执行
"""

import json
import os
import re
import sys
import time
from datetime import datetime

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
TIMEOUT = int(os.getenv("ANYROUTER_TIMEOUT", "30"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
VERIFY_SSL = os.getenv("ANYROUTER_VERIFY_SSL", "true").lower() == "true"
MAX_RETRIES = int(os.getenv("ANYROUTER_MAX_RETRIES", "3"))
BASE_URL = os.getenv("ANYROUTER_BASE_URL", "https://anyrouter.top")  # 支持自定义域名


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
    accounts_str = os.getenv('ANYROUTER_ACCOUNTS')
    if not accounts_str:
        print('❌ 未设置 ANYROUTER_ACCOUNTS 环境变量')
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

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                user_data = data.get('data', {})
                quota = round(user_data.get('quota', 0) / 500000, 2)
                used_quota = round(user_data.get('used_quota', 0) / 500000, 2)
                return True, f'当前余额: ${quota}, 已使用: ${used_quota}'
        return False, None
    except Exception as e:
        if DEBUG_MODE:
            print(f'  [DEBUG] 获取用户信息失败: {str(e)[:50]}...')
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
        return "error", "未找到 API 用户标识", None

    # 解析用户 cookies
    user_cookies = parse_cookies(cookies_data)
    if not user_cookies:
        print(f'{account_name}: ❌ 配置格式无效')
        return "error", "配置格式无效", None

    # 构建会话
    session = build_session(user_cookies, api_user)

    try:
        user_info_text = None

        # 步骤1：获取基础 WAF cookies
        get_basic_waf_cookies(session)

        # 步骤2：获取用户信息
        success, user_info = get_user_info(session)
        if success and user_info:
            print(f"  💰 {user_info}")
            user_info_text = user_info

        # 步骤3：执行签到
        print(f"  🎯 执行签到...")

        # 执行签到请求
        checkin_headers = {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
        session.headers.update(checkin_headers)

        checkin_url = f'{BASE_URL}/api/user/sign_in'
        response = session.post(checkin_url, timeout=TIMEOUT)

        if DEBUG_MODE:
            print(f'  [DEBUG] 签到响应状态码: {response.status_code}')
            print(f'  [DEBUG] 响应前100字符: {response.text[:100]}')

        # 检查是否遇到 WAF 挑战
        if response.status_code == 200 and '<script>' in response.text and 'arg1=' in response.text:
            # 尝试使用 execjs 解决 WAF 挑战
            if execute_waf_challenge(session, response.text, checkin_url):
                # WAF 挑战成功，重新请求
                time.sleep(1)
                response = session.post(checkin_url, timeout=TIMEOUT)

                if DEBUG_MODE:
                    print(f'  [DEBUG] 重试签到响应状态码: {response.status_code}')
                    print(f'  [DEBUG] 重试响应前100字符: {response.text[:100]}')
            else:
                return "fail", "WAF 挑战失败", user_info_text

        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('ret') == 1 or result.get('code') == 0 or result.get('success'):
                    msg = result.get('msg', result.get('message', '签到成功'))
                    return "success", msg, user_info_text
                else:
                    error_msg = result.get('msg', result.get('message', '未知错误'))
                    return "fail", error_msg, user_info_text
            except json.JSONDecodeError:
                # 如果不是 JSON 响应，检查是否包含成功标识
                if 'success' in response.text.lower():
                    return "success", "签到成功", user_info_text
                else:
                    if DEBUG_MODE:
                        print(f'  [DEBUG] 无法解析响应为 JSON')
                    return "fail", "响应格式无效", user_info_text
        else:
            return "fail", f"HTTP {response.status_code}", user_info_text

    except requests.exceptions.Timeout:
        return "error", f"请求超时（{TIMEOUT}秒）", user_info_text
    except requests.exceptions.ConnectionError as e:
        return "error", f"连接失败: {str(e)[:80]}", user_info_text
    except Exception as e:
        error_msg = f"{e.__class__.__name__}: {str(e)[:100]}"
        print(f'{account_name}: ❌ 签到过程中出错 - {error_msg}')
        return "error", error_msg, user_info_text
    finally:
        session.close()


def main():
    """主函数"""
    print(f"{'='*50}")
    print(f"  AnyRouter 签到脚本 v1.0")
    print(f"  执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if DEBUG_MODE:
        print(f"  🐛 调试模式: 已启用")
    print(f"{'='*50}\n")

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
            status, msg, user_info = check_in_account(account, i)

            if status == "success":
                success_count += 1
                print(f"✅ {name} 签到成功: {msg}")
                if user_info:
                    print(f"💰 {user_info}")

                safe_send_notify("AnyRouter 签到成功", f"{name}：{msg}")

            elif status == "fail":
                fail_count += 1
                print(f"⚠️ {name} 签到失败: {msg}")
                if user_info:
                    print(f"💰 {user_info}")

                safe_send_notify("AnyRouter 签到失败", f"{name}：{msg}")

            else:  # error
                error_count += 1
                print(f"❌ {name} 签到出错: {msg}")

                safe_send_notify("AnyRouter 签到出错", f"{name}：{msg}")

        except Exception as e:
            error_count += 1
            error_msg = f"{e.__class__.__name__}: {str(e)[:50]}"
            print(f"❌ {name} 处理异常: {error_msg}")
            safe_send_notify("AnyRouter 签到异常", f"{name}：{error_msg}")

        # 账号间延迟
        if i < len(accounts) - 1:
            time.sleep(3)

    print(f"\n{'='*50}")
    print(f"  所有账号签到完成")
    print(f"  ✅ 成功: {success_count} | ⚠️ 失败: {fail_count} | ❌ 出错: {error_count}")
    print(f"  完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    # 发送汇总通知（仅多账号时）
    if len(accounts) > 1:
        summary = f"签到完成\n✅ 成功: {success_count} | ⚠️ 失败: {fail_count} | ❌ 出错: {error_count}"
        safe_send_notify("AnyRouter 签到汇总", summary)

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
