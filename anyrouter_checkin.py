#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cron "0 9 * * *" script-path=anyrouter_checkin.py,tag=AnyRouter签到
new Env('AnyRouter签到')

AnyRouter.top 自动签到青龙脚本
适用于青龙面板定时任务执行
"""

import sys
import io

# 设置标准输出编码为UTF-8（解决Windows环境emoji显示问题）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import os
import random
import re
import time
from datetime import datetime

# 时区支持
try:
    from zoneinfo import ZoneInfo
    BEIJING_TZ = ZoneInfo("Asia/Shanghai")
except ImportError:
    BEIJING_TZ = None

import requests

# 导入 execjs（用于执行 WAF JavaScript）
try:
    import execjs
    HAS_EXECJS = True
except ImportError:
    HAS_EXECJS = False


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

# ---------------- 通知模块动态加载 ----------------
hadsend = False
send = None
try:
    from notify import send
    hadsend = True
    logger.info("通知模块加载成功")
except ImportError:
    logger.info("未加载通知模块，跳过通知功能")
except Exception as e:
    logger.error(f"通知模块加载失败: {e}")

if not HAS_EXECJS:
    logger.warning("未安装 PyExecJS，WAF 挑战可能失败")
    logger.warning("   安装方法：pip install PyExecJS")


# ---------------- 配置项 ----------------
TIMEOUT = int(os.getenv("ANYROUTER_TIMEOUT", "30"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
VERIFY_SSL = os.getenv("ANYROUTER_VERIFY_SSL", "true").lower() == "true"
MAX_RETRIES = int(os.getenv("ANYROUTER_MAX_RETRIES", "3"))
BASE_URL = os.getenv("ANYROUTER_BASE_URL") or "https://anyrouter.top"  # 支持自定义域名


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


def load_accounts():
    """从环境变量加载多账号配置"""
    logger.info("开始加载账号配置...")

    accounts_str = os.getenv('ANYROUTER_ACCOUNTS')
    if not accounts_str:
        logger.error('未设置 ANYROUTER_ACCOUNTS 环境变量')
        return None

    try:
        accounts_data = json.loads(accounts_str)

        # 检查是否为数组格式
        if not isinstance(accounts_data, list):
            logger.error('账号配置必须使用数组格式 [{}]')
            return None

        # 验证账号数据格式
        for i, account in enumerate(accounts_data):
            if not isinstance(account, dict):
                logger.error(f'账号 {i + 1} 配置格式不正确')
                return None
            if 'cookies' not in account or 'api_user' not in account:
                logger.error(f'账号 {i + 1} 缺少必需字段 (cookies, api_user)')
                return None

        logger.info(f"账号配置加载成功，共 {len(accounts_data)} 个账号")
        return accounts_data
    except Exception as e:
        logger.error(f'账号配置格式不正确: {e}')
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
    """获取用户信息，返回 (成功状态, 余额信息字符串, 用户名, quota, used_quota)"""
    try:
        user_info_url = f'{BASE_URL}/api/user/self'
        response = session.get(user_info_url, timeout=TIMEOUT)

        logger.debug(f"API 请求：GET {user_info_url} {response.status_code}")
        logger.debug(f"响应：{response.text[:300]}")

        # 检查是否遇到 WAF 挑战
        if response.status_code == 200 and '<script>' in response.text and 'arg1=' in response.text:
            logger.debug('用户信息接口遇到 WAF 挑战，尝试解决...')
            if execute_waf_challenge(session, response.text, user_info_url):
                time.sleep(1)
                response = session.get(user_info_url, timeout=TIMEOUT)
                logger.debug(f"API 请求：GET {user_info_url} {response.status_code}")
                logger.debug(f"响应：{response.text[:300]}")
            else:
                logger.debug('用户信息接口 WAF 挑战失败')
                return False, None, None, 0, 0

        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success'):
                    user_data = data.get('data', {})
                    quota = round(user_data.get('quota', 0) / 500000, 2)
                    used_quota = round(user_data.get('used_quota', 0) / 500000, 2)
                    username = user_data.get('display_name') or user_data.get('username', '未知用户')

                    logger.debug(f'用户名: {username}')
                    logger.debug(f'解析余额 - quota: {user_data.get("quota", 0)} -> ${quota}')
                    logger.debug(f'解析已用 - used_quota: {user_data.get("used_quota", 0)} -> ${used_quota}')

                    balance_info = f'当前余额: ${quota}, 已使用: ${used_quota}'
                    return True, balance_info, username, quota, used_quota
                else:
                    logger.debug('用户信息API返回success=false')
            except json.JSONDecodeError:
                logger.debug('用户信息响应无法解析为JSON')
        else:
            logger.debug(f'用户信息请求失败，状态码: {response.status_code}')

        return False, None, None, 0, 0
    except Exception as e:
        logger.debug(f'获取用户信息异常: {str(e)}')
        return False, None, None, 0, 0


def get_basic_waf_cookies(session):
    """获取基础 WAF cookies（通过访问登录页）"""
    try:
        logger.info("访问登录页获取基础 WAF cookies...")

        # 访问登录页面获取基础 WAF cookies（acw_tc, cdn_sec_tc）
        response = session.get(f'{BASE_URL}/login', timeout=TIMEOUT, allow_redirects=True)

        logger.debug(f"API 请求：GET {BASE_URL}/login {response.status_code}")
        logger.debug(f"当前 cookies: {list(session.cookies.keys())}")

        # 等待一下让 cookies 生效
        time.sleep(1)

        logger.info("基础 WAF cookies 获取成功")
        return True

    except Exception as e:
        logger.debug(f'获取基础 WAF cookies 失败: {str(e)[:50]}')
        return False


def execute_waf_challenge(session, challenge_html, url):
    """执行 WAF JavaScript 挑战"""
    if not HAS_EXECJS:
        logger.error("未安装 PyExecJS，无法处理 WAF 挑战")
        return False

    try:
        logger.info("检测到 WAF 挑战，尝试解决...")

        # 提取 JavaScript 代码
        js_match = re.search(r'<script>(.*?)</script>', challenge_html, re.DOTALL)
        if not js_match:
            logger.debug('未找到 JavaScript 挑战代码')
            return False

        js_code = js_match.group(1)

        logger.debug(f'WAF JavaScript 长度: {len(js_code)}')

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

        logger.debug(f'JavaScript 执行结果: {result[:100] if result else "None"}...')

        # 解析 cookie
        if result and 'acw_sc__v2=' in result:
            # 提取 acw_sc__v2 的值
            cookie_match = re.search(r'acw_sc__v2=([^;]+)', result)
            if cookie_match:
                acw_sc_v2 = cookie_match.group(1)
                session.cookies.set('acw_sc__v2', acw_sc_v2)
                logger.info('WAF 挑战已解决')
                logger.debug(f'设置 acw_sc__v2: {acw_sc_v2[:20]}...')
                return True

        logger.debug('未能从 JavaScript 结果中提取 acw_sc__v2')
        return False

    except Exception as e:
        logger.error(f'执行 WAF 挑战失败: {str(e)[:100]}')
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
        return False


def check_in_account(account_info, account_index):
    """为单个账号执行签到操作"""
    account_name = f'账号{account_index + 1}'
    logger.info(f"\n==== {account_name} 开始签到 ====")
    logger.info(f"当前时间: {datetime.now().strftime('%H:%M:%S')}")

    # 解析账号配置
    cookies_data = account_info.get('cookies', {})
    api_user = account_info.get('api_user', '')

    if not api_user:
        logger.error(f'{account_name}: 未找到 API 用户标识')
        return "error", "未找到 API 用户标识", None, 0, None

    # 解析用户 cookies
    user_cookies = parse_cookies(cookies_data)
    if not user_cookies:
        logger.error(f'{account_name}: 配置格式无效')
        return "error", "配置格式无效", None, 0, None

    # 构建会话
    session = build_session(user_cookies, api_user)

    try:
        # 步骤1：获取基础 WAF cookies
        get_basic_waf_cookies(session)

        # 步骤2：获取签到前的用户信息
        logger.info("获取签到前信息...")
        before_success, before_info, username, before_quota, before_used = get_user_info(session)

        if before_success and before_info:
            logger.info(f"用户: {username}")
            logger.info(f"签到前: {before_info}")

        # 步骤3：执行签到
        logger.info("执行签到...")
        checkin_headers = {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
        session.headers.update(checkin_headers)

        checkin_url = f'{BASE_URL}/api/user/sign_in'
        response = session.post(checkin_url, timeout=TIMEOUT)

        logger.debug(f"API 请求：POST {checkin_url} {response.status_code}")
        logger.debug(f"响应：{response.text[:300]}")

        # 检查是否遇到 WAF 挑战
        if response.status_code == 200 and '<script>' in response.text and 'arg1=' in response.text:
            if execute_waf_challenge(session, response.text, checkin_url):
                time.sleep(1)
                response = session.post(checkin_url, timeout=TIMEOUT)
                logger.debug(f"API 请求：POST {checkin_url} {response.status_code}")
                logger.debug(f"响应：{response.text[:300]}")
            else:
                return "fail", "WAF 挑战失败", None, 0, username

        if response.status_code == 200:
            try:
                result = response.json()

                logger.debug(f'签到响应JSON: {json.dumps(result, ensure_ascii=False, indent=2)}')

                if result.get('ret') == 1 or result.get('code') == 0 or result.get('success'):
                    # 步骤4：获取签到后的用户信息（计算余额变化）
                    logger.info("获取签到后余额...")
                    time.sleep(1)
                    after_success, after_info, after_username, after_quota, after_used = get_user_info(session)
                    reward_amount = 0

                    if after_success and after_info:
                        logger.info(f"签到后: {after_info}")

                        # 使用签到后的用户名（更准确）
                        if after_username:
                            username = after_username

                        # 计算奖励金额（总余额的增加）
                        if before_success:
                            reward_amount = (after_quota + after_used) - (before_quota + before_used)
                            if reward_amount > 0:
                                # 有奖励，说明刚签到成功
                                logger.info(f"签到奖励: ${reward_amount:.2f}")
                                msg = f"签到成功，获得 ${reward_amount:.2f}"
                            else:
                                # 无奖励，说明今日已签到
                                msg = "今日已签到"
                                logger.info(msg)
                        else:
                            # 签到前获取余额失败，使用接口返回的消息
                            msg = result.get('msg') or result.get('message') or '签到成功'

                        logger.info(f"签到完成，结果：{msg}")
                        return "success", msg, after_info, reward_amount, username
                    else:
                        # 签到成功但获取余额失败，使用接口返回的消息
                        msg = result.get('msg') or result.get('message') or '签到成功'
                        logger.info(f"签到完成，结果：{msg}")
                        return "success", msg, before_info if before_success else None, 0, username
                else:
                    error_msg = result.get('msg') or result.get('message') or '未知错误'
                    logger.error(f"签到失败，原因：{error_msg}")
                    return "fail", error_msg, before_info if before_success else None, 0, username
            except json.JSONDecodeError:
                if 'success' in response.text.lower():
                    logger.info("签到完成，结果：签到成功")
                    return "success", "签到成功", before_info if before_success else None, 0, username
                else:
                    logger.debug('无法解析响应为 JSON')
                    return "fail", "响应格式无效", before_info if before_success else None, 0, username

        elif response.status_code == 404:
            # 404保活逻辑：签到接口不存在，尝试查询用户信息进行保活
            logger.info("签到接口返回404，尝试查询用户信息进行保活...")
            try:
                # 使用用户信息接口进行保活
                user_info_url = f'{BASE_URL}/api/user/self'
                user_resp = session.get(user_info_url, timeout=TIMEOUT)

                logger.debug(f"API 请求：GET {user_info_url} {user_resp.status_code}")
                logger.debug(f"响应：{user_resp.text[:300]}")

                if user_resp.status_code == 200:
                    user_data = user_resp.json()
                    if user_data.get('success'):
                        logger.info("用户信息查询成功，账号已保活")

                        # 获取用户余额信息用于通知
                        quota = round(user_data.get('data', {}).get('quota', 0) / 500000, 2)
                        used_quota = round(user_data.get('data', {}).get('used_quota', 0) / 500000, 2)
                        user_info = f'当前余额: ${quota}, 已使用: ${used_quota}'

                        return "success", "签到接口不存在，但账号状态正常", user_info, 0, username
                    else:
                        logger.warning(f"用户信息查询失败: {user_data.get('message', 'Unknown error')}")
                        return "fail", f"签到接口404，用户信息查询失败", before_info if before_success else None, 0, username
                else:
                    logger.warning(f"用户信息接口返回 {user_resp.status_code}")
                    return "fail", f"签到接口404，用户信息接口返回{user_resp.status_code}", before_info if before_success else None, 0, username

            except Exception as e:
                logger.warning(f"用户信息查询异常: {e}")
                return "fail", "签到接口404，用户信息查询也失败", before_info if before_success else None, 0, username

        else:
            logger.error(f"签到失败，HTTP状态码: {response.status_code}")
            return "fail", f"HTTP {response.status_code}", before_info if before_success else None, 0, username

    except requests.exceptions.Timeout:
        logger.error(f"请求超时（{TIMEOUT}秒）")
        return "error", f"请求超时（{TIMEOUT}秒）", None, 0, None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"连接失败: {str(e)[:80]}")
        return "error", f"连接失败: {str(e)[:80]}", None, 0, None
    except Exception as e:
        error_msg = f"{e.__class__.__name__}: {str(e)[:100]}"
        logger.error(f'{account_name}: 签到过程中出错 - {error_msg}')
        return "error", error_msg, None, 0, None
    finally:
        session.close()


def main():
    """主函数"""
    logger.info("="*50)
    logger.info("  AnyRouter 签到脚本 v1.0")
    logger.info(f"  执行时间: {now_beijing().strftime('%Y-%m-%d %H:%M:%S')}")
    if DEBUG_MODE:
        logger.info("  调试模式: 已启用")
    logger.info("="*50)

    # 加载账号配置
    accounts = load_accounts()
    if not accounts:
        logger.error('无法加载账号配置，程序退出')
        sys.exit(1)

    logger.info(f"共发现 {len(accounts)} 个账号配置")
    logger.info("==== 开始执行签到任务 ====")

    # 为每个账号执行签到
    success_count = 0
    fail_count = 0
    error_count = 0

    for i, account in enumerate(accounts):
        name = f"账号{i + 1}"

        try:
            status, msg, user_info, reward, username = check_in_account(account, i)

            if status == "success":
                success_count += 1
                logger.info(f"{name} 签到成功: {msg}")
                if user_info:
                    logger.info(f"{user_info}")

                # 统一通知格式
                notify_content = f"""🌐 域名：{BASE_URL.replace('https://', '').replace('http://', '')}

👤 {name}："""

                if username:
                    notify_content += f"\n📱 用户：{username}"

                notify_content += f"\n📝 签到：{msg}"

                if user_info:
                    notify_content += f"\n💰 账户：{user_info}"

                notify_content += f"\n⏰ 时间：{now_beijing().strftime('%Y-%m-%d %H:%M:%S')}"

                safe_send_notify("[AnyRouter]签到成功", notify_content)

            elif status == "fail":
                fail_count += 1
                logger.warning(f"{name} 签到失败: {msg}")
                if user_info:
                    logger.info(f"{user_info}")

                # 统一通知格式
                notify_content = f"""🌐 域名：{BASE_URL.replace('https://', '').replace('http://', '')}

👤 {name}："""

                if username:
                    notify_content += f"\n📱 用户：{username}"

                notify_content += f"\n📝 签到：{msg}"

                if user_info:
                    notify_content += f"\n💰 账户：{user_info}"

                notify_content += f"\n⏰ 时间：{now_beijing().strftime('%Y-%m-%d %H:%M:%S')}"

                safe_send_notify("[AnyRouter]签到失败", notify_content)

            else:  # error
                error_count += 1
                logger.error(f"{name} 签到出错: {msg}")

                # 统一通知格式
                notify_content = f"""🌐 域名：{BASE_URL.replace('https://', '').replace('http://', '')}

👤 {name}："""

                if username:
                    notify_content += f"\n📱 用户：{username}"

                notify_content += f"\n📝 签到：签到出错 - {msg}\n⏰ 时间：{now_beijing().strftime('%Y-%m-%d %H:%M:%S')}"

                safe_send_notify("[AnyRouter]签到出错", notify_content)

        except Exception as e:
            error_count += 1
            error_msg = f"{e.__class__.__name__}: {str(e)[:50]}"
            logger.error(f"{name} 处理异常: {error_msg}")

            # 统一通知格式
            notify_content = f"""🌐 域名：{BASE_URL.replace('https://', '').replace('http://', '')}

👤 {name}：
📝 签到：签到异常 - {error_msg}
⏰ 时间：{now_beijing().strftime('%Y-%m-%d %H:%M:%S')}"""

            safe_send_notify("[AnyRouter]签到异常", notify_content)

        # 账号间延迟
        if i < len(accounts) - 1:
            time.sleep(3)

    logger.info("="*50)
    logger.info("  所有账号签到完成")
    logger.info(f"  成功: {success_count} | 失败: {fail_count} | 出错: {error_count}")
    logger.info(f"  完成时间: {now_beijing().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*50)

    # 发送汇总通知（仅多账号时，统一格式）
    if len(accounts) > 1:
        summary = f"""🌐 域名：{BASE_URL.replace('https://', '').replace('http://', '')}

📊 签到汇总：
✅ 成功：{success_count}个
⚠️ 失败：{fail_count}个
❌ 出错：{error_count}个
📈 成功率：{success_count/len(accounts)*100:.1f}%
⏰ 完成时间：{now_beijing().strftime('%Y-%m-%d %H:%M:%S')}"""

        safe_send_notify("[AnyRouter]签到汇总", summary)

    # 设置退出码
    sys.exit(0 if success_count > 0 else 1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning('程序被用户中断')
        sys.exit(1)
    except Exception as e:
        logger.error(f'程序执行过程中发生错误: {e}')
        sys.exit(1)
