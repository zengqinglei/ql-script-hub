#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cron "0 9 * * *" script-path=newapi_checkin.py,tag=NewAPI签到
new Env('NewAPI签到')

NewAPI 通用签到脚本
支持所有基于 NewAPI 二次开发的站点（GemAI、AnyRouter、AgentRouter、996Coder 等）

认证方式通过账号字段自动判断：
  - 含 cookies 字段 → Cookie 模式（requests 直接调 API）
  - 含 email 字段   → 浏览器模式（Playwright 模拟登录）

签到接口：
  - checkin_path 字段指定，默认 fallback = /api/user/checkin
  - checkin_path = "" 表示登录即触发签到，不主动调用接口
"""

import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import asyncio
import json
import os
import re
import tempfile
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

try:
    from zoneinfo import ZoneInfo
    BEIJING_TZ = ZoneInfo("Asia/Shanghai")
except ImportError:
    BEIJING_TZ = None


# ==================== 日志 ====================
class Logger:
    def __init__(self):
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"

    def log(self, level, message):
        if BEIJING_TZ:
            ts = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")
        else:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{ts} {level} {message}")

    def info(self, msg):    self.log("INFO", msg)
    def warning(self, msg): self.log("WARNING", msg)
    def error(self, msg):   self.log("ERROR", msg)
    def debug(self, msg):
        if self.debug_mode:
            self.log("DEBUG", msg)


logger = Logger()
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"


def now_beijing():
    if BEIJING_TZ:
        return datetime.now(BEIJING_TZ)
    return datetime.now()


# ==================== 通知 ====================
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


def safe_send_notify(title: str, content: str):
    if hadsend:
        try:
            send(title, content)
            logger.info(f"通知推送成功: {title}")
        except Exception as e:
            logger.error(f"通知推送失败: {e}")
    else:
        logger.info(f"通知: {title}")


# ==================== 全局配置 ====================
TIMEOUT = int(os.getenv("NEWAPI_TIMEOUT", "30"))
VERIFY_SSL = os.getenv("NEWAPI_VERIFY_SSL", "true").lower() == "true"
MAX_RETRIES = int(os.getenv("NEWAPI_MAX_RETRIES", "3"))
BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
QUOTA_TO_DOLLAR = 500000
DEFAULT_CHECKIN_PATH = "/api/user/checkin"

# WAF 相关
try:
    import execjs
    HAS_EXECJS = True
except ImportError:
    HAS_EXECJS = False
    logger.warning("未安装 PyExecJS，Cookie 模式 WAF 挑战可能失败（pip install PyExecJS）")

# Playwright（浏览器模式可选依赖）
try:
    from playwright.async_api import async_playwright, Page, BrowserContext
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# httpx（浏览器模式可选依赖）
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ==================== 账号加载 ====================
def load_accounts() -> Optional[List[Dict]]:
    logger.info("开始加载账号配置...")
    accounts_str = os.getenv("NEWAPI_ACCOUNTS")
    if not accounts_str:
        logger.error("未设置 NEWAPI_ACCOUNTS 环境变量")
        return None
    try:
        accounts = json.loads(accounts_str)
        if not isinstance(accounts, list):
            logger.error("NEWAPI_ACCOUNTS 必须为 JSON 数组格式")
            return None
        for i, acc in enumerate(accounts):
            if not isinstance(acc, dict):
                logger.error(f"账号 {i+1} 格式不正确")
                return None
            if "base_url" not in acc:
                logger.error(f"账号 {i+1} 缺少 base_url 字段")
                return None
            has_cookie = "cookies" in acc and "api_user" in acc
            has_email  = "email" in acc and "password" in acc
            if not has_cookie and not has_email:
                logger.error(f"账号 {i+1} 缺少认证字段：需要 (cookies+api_user) 或 (email+password)")
                return None
        logger.info(f"账号配置加载成功，共 {len(accounts)} 个账号")
        return accounts
    except Exception as e:
        logger.error(f"账号配置解析失败: {e}")
        return None


def get_account_mode(account: Dict) -> str:
    """通过字段自动判断认证模式"""
    if "cookies" in account and "api_user" in account:
        return "cookie"
    return "browser"


def get_checkin_path(account: Dict) -> str:
    """获取签到路径，账号配置优先，否则 fallback 默认值"""
    if "checkin_path" in account:
        return account["checkin_path"]
    return DEFAULT_CHECKIN_PATH


def get_display_domain(base_url: str) -> str:
    return base_url.replace("https://", "").replace("http://", "").rstrip("/")


# ==================== Cookie 模式 ====================

def parse_cookies(cookies_data) -> Dict:
    if isinstance(cookies_data, dict):
        return cookies_data
    if isinstance(cookies_data, str):
        result = {}
        for part in cookies_data.split(";"):
            if "=" in part:
                k, v = part.strip().split("=", 1)
                result[k] = v
        return result
    return {}


def build_session(base_url: str, cookies_dict: Dict, api_user: str) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "POST", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.verify = VERIFY_SSL
    if not VERIFY_SSL:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": f"{base_url}/console",
        "Origin": base_url,
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "New-Api-User": api_user,
    })
    for name, value in cookies_dict.items():
        session.cookies.set(name, value)
    return session


def execute_waf_challenge(session: requests.Session, challenge_html: str, url: str, base_url: str) -> bool:
    if not HAS_EXECJS:
        logger.error("未安装 PyExecJS，无法处理 WAF 挑战")
        return False
    try:
        logger.info("检测到 WAF 挑战，尝试解决...")
        js_match = re.search(r"<script>(.*?)</script>", challenge_html, re.DOTALL)
        if not js_match:
            return False
        js_code = js_match.group(1)
        parsed_base = urlparse(base_url)
        base_host = parsed_base.netloc
        parsed_url = urlparse(url)
        url_pathname = parsed_url.path
        js_env = f"""
        var document = {{
            cookie: '',
            set cookie(val) {{ this._cookie = val; }},
            get cookie() {{ return this._cookie || ''; }},
            getElementById: function() {{ return null; }},
            getElementsByTagName: function() {{ return []; }},
            createElement: function() {{ return {{}}; }},
            body: {{}}, head: {{}}
        }};
        var location = {{
            href: '{url}', protocol: '{parsed_url.scheme}:',
            host: '{base_host}', hostname: '{base_host}', port: '',
            pathname: '{url_pathname}', search: '', hash: '',
            origin: '{base_url}',
            reload: function() {{}}, replace: function() {{}},
            assign: function() {{}}, toString: function() {{ return this.href; }}
        }};
        var navigator = {{
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            platform: 'Win32', language: 'zh-CN',
            languages: ['zh-CN', 'zh', 'en'], onLine: true, cookieEnabled: true
        }};
        var window = this;
        window.location = location; window.document = document; window.navigator = navigator;
        window.setTimeout = function(fn, delay) {{ if (typeof fn === 'function') try {{ fn(); }} catch(e) {{}} }};
        window.setInterval = function() {{}};
        window.clearTimeout = function() {{}};
        window.clearInterval = function() {{}};
        window.addEventListener = function() {{}};
        window.removeEventListener = function() {{}};
        try {{ {js_code} }} catch(e) {{}}
        document.cookie;
        """
        ctx = execjs.compile(js_env)
        result = ctx.eval("document.cookie")
        if result and "acw_sc__v2=" in result:
            m = re.search(r"acw_sc__v2=([^;]+)", result)
            if m:
                session.cookies.set("acw_sc__v2", m.group(1))
                logger.info("WAF 挑战已解决")
                return True
        return False
    except Exception as e:
        logger.error(f"执行 WAF 挑战失败: {str(e)[:100]}")
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
        return False


def get_user_info_cookie(session: requests.Session, base_url: str) -> Tuple[bool, Optional[str], Optional[str], float, float]:
    """获取用户信息，返回 (ok, balance_str, username, quota, used_quota)"""
    try:
        url = f"{base_url}/api/user/self"
        resp = session.get(url, timeout=TIMEOUT)
        logger.debug(f"GET {url} -> {resp.status_code}")
        logger.debug(f"响应: {resp.text[:300]}")
        if resp.status_code == 200 and "<script>" in resp.text and "arg1=" in resp.text:
            if execute_waf_challenge(session, resp.text, url, base_url):
                time.sleep(1)
                resp = session.get(url, timeout=TIMEOUT)
            else:
                return False, None, None, 0, 0
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                ud = data.get("data", {})
                quota = round(ud.get("quota", 0) / QUOTA_TO_DOLLAR, 2)
                used  = round(ud.get("used_quota", 0) / QUOTA_TO_DOLLAR, 2)
                username = ud.get("display_name") or ud.get("username", "未知用户")
                return True, f"当前余额: ${quota}, 已使用: ${used}", username, quota, used
        return False, None, None, 0, 0
    except Exception as e:
        logger.debug(f"获取用户信息异常: {e}")
        return False, None, None, 0, 0


def checkin_cookie_mode(account: Dict, account_name: str) -> Tuple[str, str, Optional[str], float, Optional[str]]:
    """Cookie 模式签到，返回 (status, msg, balance_info, reward, username)"""
    base_url     = account["base_url"].rstrip("/")
    cookies_data = account.get("cookies", {})
    api_user     = account.get("api_user", "")
    checkin_path = get_checkin_path(account)

    if not api_user:
        return "error", "缺少 api_user 字段", None, 0, None

    cookies_dict = parse_cookies(cookies_data)
    if not cookies_dict:
        return "error", "cookies 格式无效", None, 0, None

    session = build_session(base_url, cookies_dict, api_user)
    try:
        # 获取基础 WAF cookies
        try:
            session.get(f"{base_url}/login", timeout=TIMEOUT, allow_redirects=True)
            time.sleep(1)
        except Exception:
            pass

        # 签到前余额
        before_ok, before_info, username, before_quota, before_used = get_user_info_cookie(session, base_url)
        if before_ok:
            logger.info(f"用户: {username}")
            logger.info(f"签到前: {before_info}")

        # 若 checkin_path 为空，仅保活
        if checkin_path == "":
            if before_ok:
                return "success", "账号状态正常（无独立签到接口）", before_info, 0, username
            return "fail", "无法获取账号状态", None, 0, username

        # 执行签到
        logger.info("执行签到...")
        session.headers.update({"Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest"})
        checkin_url = f"{base_url}{checkin_path}"
        resp = session.post(checkin_url, timeout=TIMEOUT)
        logger.debug(f"POST {checkin_url} -> {resp.status_code}")
        logger.debug(f"响应: {resp.text[:300]}")

        if resp.status_code == 200 and "<script>" in resp.text and "arg1=" in resp.text:
            if execute_waf_challenge(session, resp.text, checkin_url, base_url):
                time.sleep(1)
                resp = session.post(checkin_url, timeout=TIMEOUT)
            else:
                return "fail", "WAF 挑战失败", None, 0, username

        if resp.status_code == 200:
            try:
                result = resp.json()
                logger.debug(f"签到响应: {json.dumps(result, ensure_ascii=False)}")
                if result.get("ret") == 1 or result.get("code") == 0 or result.get("success"):
                    time.sleep(1)
                    after_ok, after_info, after_username, after_quota, after_used = get_user_info_cookie(session, base_url)
                    reward = 0
                    if after_ok:
                        if after_username:
                            username = after_username
                        if before_ok:
                            reward = (after_quota + after_used) - (before_quota + before_used)
                            msg = f"签到成功，获得 ${reward:.2f}" if reward > 0 else "今日已签到"
                        else:
                            msg = result.get("msg") or result.get("message") or "签到成功"
                        logger.info(f"签到后: {after_info}")
                        return "success", msg, after_info, reward, username
                    else:
                        msg = result.get("msg") or result.get("message") or "签到成功"
                        return "success", msg, before_info if before_ok else None, 0, username
                else:
                    error_msg = result.get("msg") or result.get("message") or "未知错误"
                    if "已签到" in error_msg or "already" in error_msg.lower():
                        return "success", "今日已签到", before_info if before_ok else None, 0, username
                    return "fail", error_msg, before_info if before_ok else None, 0, username
            except json.JSONDecodeError:
                if "success" in resp.text.lower():
                    return "success", "签到成功", before_info if before_ok else None, 0, username
                return "fail", "响应格式无效", before_info if before_ok else None, 0, username

        elif resp.status_code == 404:
            # 404 保活：查用户信息
            logger.info("签到接口返回 404，尝试查询用户信息保活...")
            ok, info, _, quota, used = get_user_info_cookie(session, base_url)
            if ok:
                return "success", "签到接口不存在，但账号状态正常", info, 0, username
            return "fail", "签到接口 404，用户信息查询也失败", before_info if before_ok else None, 0, username
        else:
            return "fail", f"HTTP {resp.status_code}", before_info if before_ok else None, 0, username

    except requests.exceptions.Timeout:
        return "error", f"请求超时（{TIMEOUT}秒）", None, 0, None
    except requests.exceptions.ConnectionError as e:
        return "error", f"连接失败: {str(e)[:80]}", None, 0, None
    except Exception as e:
        return "error", f"{e.__class__.__name__}: {str(e)[:100]}", None, 0, None
    finally:
        session.close()


# ==================== 浏览器模式 ====================

BROWSER_LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--disable-web-security",
    "--no-sandbox",
    "--disable-infobars",
    "--disable-popup-blocking",
    "--disable-notifications",
    "--disable-extensions",
    "--ignore-certificate-errors",
    "--allow-running-insecure-content",
    "--disable-gpu",
    "--window-size=1280,720",
    "--disable-features=IsolateOrigins,site-per-process",
    "--disable-site-isolation-trials",
    "--disable-features=BlockInsecurePrivateNetworkRequests",
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-breakpad",
    "--disable-component-extensions-with-background-pages",
    "--disable-features=TranslateUI",
    "--disable-ipc-flooding-protection",
    "--disable-renderer-backgrounding",
    "--metrics-recording-only",
    "--mute-audio",
    "--no-first-run",
    "--disable-hang-monitor",
]

STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en-US', 'en'] });
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
  parameters.name === 'notifications' ?
    Promise.resolve({ state: Notification.permission }) :
    originalQuery(parameters)
);
Object.defineProperty(navigator, 'plugins', {
  get: () => [
    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
    { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
  ],
});
try {
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) return 'Intel Inc.';
        if (parameter === 37446) return 'Intel Iris OpenGL Engine';
        return getParameter.call(this, parameter);
    };
} catch (e) {}
if (!window.chrome) {
    window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {}, app: {} };
}
Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 1 });
Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
"""

DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
WAF_COOKIE_NAMES = ["acw_tc", "cdn_sec_tc", "acw_sc__v2"]
KEY_COOKIE_NAMES = ["session", "sessionid", "token", "auth", "jwt"]
EMAIL_SELECTORS = [
    'input[type="email"]', 'input[name="email"]',
    'input[placeholder*="邮箱"]', 'input[placeholder*="Email"]', 'input[id*="email"]',
]
PASSWORD_SELECTORS = ['input[type="password"]', 'input[name="password"]']
LOGIN_BTN_SELECTORS = [
    'button[type="submit"]', 'button:has-text("登录")',
    'button:has-text("Login")', 'input[type="submit"]',
]
POPUP_CLOSE_SELECTORS = [
    '.semi-modal-close', '[aria-label="Close"]',
    'button:has-text("关闭")', 'button:has-text("我知道了")',
]


async def _close_popups(page: "Page"):
    try:
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)
        for sel in POPUP_CLOSE_SELECTORS:
            try:
                btn = await page.query_selector(sel)
                if btn:
                    await btn.click()
                    await page.wait_for_timeout(300)
                    break
            except Exception:
                continue
    except Exception:
        pass


async def _find_input(page: "Page", selectors: List[str]):
    for sel in selectors:
        try:
            el = await page.query_selector(sel)
            if el:
                return el
        except Exception:
            continue
    return None


async def _browser_login(page: "Page", context: "BrowserContext",
                         account_name: str, base_url: str,
                         email: str, password: str) -> Dict:
    """浏览器登录，返回 {success, cookies, username, user_id}"""
    login_url = f"{base_url}/login"
    try:
        logger.info(f"{account_name}: 访问登录页 {login_url}")
        await page.goto(login_url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(2000)
        await _close_popups(page)

        # 尝试点击"邮箱登录"切换按钮
        for sel in [
            'button:has-text("使用 邮箱或用户名 登录")',
            'button:has-text("邮箱或用户名")',
            'button:has-text("邮箱登录")',
            'button:has-text("Email")',
        ]:
            try:
                btn = await page.query_selector(sel)
                if btn:
                    await btn.click()
                    await page.wait_for_timeout(1000)
                    break
            except Exception:
                continue

        email_input = await _find_input(page, EMAIL_SELECTORS)
        if not email_input:
            return {"success": False, "error": "未找到邮箱输入框"}

        pwd_input = await _find_input(page, PASSWORD_SELECTORS)
        if not pwd_input:
            return {"success": False, "error": "未找到密码输入框"}

        await email_input.fill(email)
        await page.wait_for_timeout(500)
        await pwd_input.fill(password)
        await page.wait_for_timeout(500)

        login_btn = await _find_input(page, LOGIN_BTN_SELECTORS)
        if not login_btn:
            return {"success": False, "error": "未找到登录按钮"}

        logger.info(f"{account_name}: 点击登录按钮")
        await login_btn.click()

        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
            await page.wait_for_timeout(2000)
        except Exception:
            logger.warning(f"{account_name}: 页面加载超时，继续检查登录状态")

        current_url = page.url
        logger.info(f"{account_name}: 登录后 URL: {current_url}")
        if "login" in current_url.lower():
            # 检查错误提示
            for sel in [".error", ".alert-danger", '[class*="error"]', ".toast-error", '[role="alert"]']:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        text = await el.inner_text()
                        if text and text.strip():
                            return {"success": False, "error": f"登录失败: {text.strip()}"}
                except Exception:
                    continue
            return {"success": False, "error": "登录失败，仍在登录页面"}

        # 获取 cookies
        all_cookies = await context.cookies()
        cookies_dict = {c["name"]: c["value"] for c in all_cookies}
        logger.info(f"{account_name}: 获取到 {len(cookies_dict)} 个 cookies")

        # 提取用户信息
        username, user_id = None, None
        if HAS_HTTPX:
            try:
                user_info_url = f"{base_url}/api/user/self"
                headers = {"User-Agent": DEFAULT_UA, "Accept": "application/json"}
                async with httpx.AsyncClient(cookies=cookies_dict, timeout=10.0, verify=True) as client:
                    r = await client.get(user_info_url, headers=headers)
                    if r.status_code == 200:
                        data = r.json()
                        if data.get("success") and data.get("data"):
                            ud = data["data"]
                            user_id = str(ud.get("id") or ud.get("user_id") or "")
                            username = ud.get("username") or ud.get("name") or ud.get("email")
            except Exception as e:
                logger.warning(f"{account_name}: 提取用户信息失败: {e}")

        return {"success": True, "cookies": cookies_dict, "username": username, "user_id": user_id}
    except Exception as e:
        return {"success": False, "error": f"登录异常: {str(e)}"}


async def checkin_browser_mode_async(account: Dict, account_name: str) -> Tuple[str, str, Optional[str], float, Optional[str]]:
    """浏览器模式签到（异步），返回 (status, msg, balance_info, reward, username)"""
    if not HAS_PLAYWRIGHT:
        return "error", "未安装 Playwright（pip install playwright && playwright install chromium）", None, 0, None

    base_url     = account["base_url"].rstrip("/")
    email        = account["email"]
    password     = account["password"]
    checkin_path = get_checkin_path(account)

    checkin_info     = {"found": False, "message": "", "reward": ""}
    user_balance     = {"quota": 0, "used_quota": 0, "username": "", "user_id": ""}

    async with async_playwright() as playwright:
        with tempfile.TemporaryDirectory() as tmp_dir:
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=tmp_dir,
                headless=BROWSER_HEADLESS,
                user_agent=DEFAULT_UA,
                viewport={"width": 1920, "height": 1080},
                args=BROWSER_LAUNCH_ARGS,
                java_script_enabled=True,
            )
            page = await context.new_page()
            await page.add_init_script(STEALTH_SCRIPT)
            logger.info(f"{account_name}: 已注入 Stealth 脚本")

            # 网络监听：捕获签到响应和余额
            async def handle_response(response):
                try:
                    url = response.url
                    if "/api/" not in url:
                        return
                    logger.debug(f"API {response.request.method} {url} -> {response.status}")
                    if response.status != 200:
                        return
                    try:
                        jd = await response.json()
                    except Exception:
                        return
                    if not isinstance(jd, dict):
                        return
                    logger.debug(f"响应数据: {json.dumps(jd, ensure_ascii=False)[:500]}")
                    msg = jd.get("message") or jd.get("msg") or ""
                    # 捕获签到响应
                    if (any(kw in msg.lower() for kw in ["签到", "sign", "check", "今日", "已", "成功"])
                            or "sign" in url.lower() or "checkin" in url.lower()):
                        checkin_info["found"] = True
                        checkin_info["message"] = msg or "签到成功"
                        if "data" in jd and isinstance(jd["data"], dict):
                            for key in ["reward", "amount", "quota_awarded", "quota", "balance", "credit"]:
                                if key in jd["data"]:
                                    val = jd["data"][key]
                                    if key == "quota_awarded":
                                        val_usd = round(val / QUOTA_TO_DOLLAR, 2)
                                        checkin_info["reward"] = f"${val_usd} ({val})"
                                    else:
                                        checkin_info["reward"] = str(val)
                                    break
                    # 捕获余额
                    if ("/api/user/login" in url or "/api/user/self" in url) and jd.get("success") and jd.get("data"):
                        ud = jd["data"]
                        if "quota" in ud:
                            user_balance["quota"]      = ud.get("quota", 0)
                            user_balance["used_quota"] = ud.get("used_quota", 0)
                            user_balance["username"]   = ud.get("display_name") or ud.get("username", "")
                            user_balance["user_id"]    = str(ud.get("id", ""))
                except Exception:
                    pass

            page.on("response", handle_response)

            try:
                # 获取 WAF cookies
                try:
                    await page.goto(f"{base_url}/login", wait_until="domcontentloaded", timeout=20000)
                    await page.wait_for_timeout(2000)
                    waf = [c for c in await context.cookies() if c["name"] in WAF_COOKIE_NAMES]
                    logger.info(f"{account_name}: 获取到 {len(waf)} 个 WAF cookies")
                except Exception as e:
                    logger.warning(f"{account_name}: 获取 WAF cookies 失败: {e}")

                # 登录
                auth = await _browser_login(page, context, account_name, base_url, email, password)
                if not auth["success"]:
                    return "error", auth.get("error", "登录失败"), None, 0, None

                logger.info(f"{account_name}: 登录成功")
                cookies = auth.get("cookies", {})
                username = user_balance.get("username") or auth.get("username") or ""

                # 等待网络监听捕获
                await page.wait_for_timeout(2000)

                # 主动调用签到接口（checkin_path 非空时）
                if checkin_path:
                    # 等待 user_id（最多 10 秒）
                    user_id = user_balance.get("user_id") or auth.get("user_id") or ""
                    for _ in range(10):
                        if user_id:
                            break
                        await asyncio.sleep(1)
                        user_id = user_balance.get("user_id") or ""

                    checkin_url = f"{base_url}{checkin_path}"
                    logger.info(f"{account_name}: 主动调用签到接口 POST {checkin_url}")
                    fetch_script = r"""async ({url, userId}) => {
                        try {
                            const headers = { 'Content-Type': 'application/json', 'Accept': 'application/json, text/plain, */*' };
                            if (userId) headers['New-Api-User'] = userId;
                            const resp = await fetch(url, { method: 'POST', headers });
                            return { status: resp.status, text: await resp.text() };
                        } catch (e) {
                            return { status: 0, text: e.toString() };
                        }
                    }"""
                    try:
                        cr = await page.evaluate(fetch_script, {"url": checkin_url, "userId": user_id})
                        logger.info(f"{account_name}: 签到接口响应状态: {cr['status']}")
                        logger.debug(f"{account_name}: 签到接口响应: {cr['text']}")
                        if cr["status"] == 200:
                            try:
                                jr = json.loads(cr["text"])
                                msg = jr.get("message") or jr.get("msg") or ""
                                if jr.get("success"):
                                    checkin_info["found"] = True
                                    checkin_info["message"] = msg or "签到成功"
                                    if "data" in jr and isinstance(jr["data"], dict):
                                        for key in ["quota_awarded", "reward", "amount", "quota", "balance"]:
                                            if key in jr["data"]:
                                                val = jr["data"][key]
                                                if key == "quota_awarded":
                                                    val_usd = round(val / QUOTA_TO_DOLLAR, 2)
                                                    checkin_info["reward"] = f"${val_usd} ({val})"
                                                else:
                                                    checkin_info["reward"] = str(val)
                                                break
                                elif msg:
                                    checkin_info["found"] = True
                                    checkin_info["message"] = msg
                            except Exception:
                                pass
                    except Exception as e:
                        logger.warning(f"{account_name}: 主动签到调用失败: {e}")

                    await page.wait_for_timeout(2000)

                # 汇总结果
                if checkin_info["found"]:
                    checkin_msg = checkin_info["message"]
                    if checkin_info["reward"]:
                        checkin_msg += f" | 奖励: {checkin_info['reward']}"
                else:
                    checkin_msg = "登录签到完成" if not checkin_path else "签到完成"

                quota_usd = round(user_balance["quota"] / QUOTA_TO_DOLLAR, 2)
                used_usd  = round(user_balance["used_quota"] / QUOTA_TO_DOLLAR, 2)
                balance_info = f"余额: ${quota_usd:.2f}, 已用: ${used_usd:.2f}" if (quota_usd or used_usd) else None

                if balance_info:
                    logger.info(f"{account_name}: {balance_info}")

                return "success", checkin_msg, balance_info, 0, username or None

            finally:
                await page.close()
                await context.close()


# ==================== 统一调度 ====================

def checkin_account(account: Dict, index: int) -> Dict:
    """对单个账号执行签到，返回结果 dict"""
    account_name = account.get("name", f"账号{index + 1}")
    base_url     = account["base_url"].rstrip("/")
    mode         = get_account_mode(account)
    domain       = get_display_domain(base_url)

    logger.info(f"\n{'='*60}")
    logger.info(f"{account_name}: 开始签到 [{mode} 模式] {domain}")
    logger.info(f"{'='*60}")

    try:
        if mode == "cookie":
            status, msg, balance_info, reward, username = checkin_cookie_mode(account, account_name)
        else:
            status, msg, balance_info, reward, username = asyncio.run(
                checkin_browser_mode_async(account, account_name)
            )
    except Exception as e:
        status, msg, balance_info, reward, username = "error", f"{e.__class__.__name__}: {str(e)[:100]}", None, 0, None

    return {
        "account": account_name,
        "domain":  domain,
        "mode":    mode,
        "status":  status,
        "msg":     msg,
        "balance": balance_info,
        "reward":  reward,
        "username": username,
    }


def build_notify_content(result: Dict, ts: str) -> str:
    lines = [f"🌐 域名：{result['domain']}", ""]
    lines.append(f"👤 {result['account']}：")
    if result.get("username"):
        lines.append(f"📱 用户：{result['username']}")
    lines.append(f"📝 签到：{result['msg']}")
    if result.get("balance"):
        lines.append(f"💰 账户：{result['balance']}")
    lines.append(f"⏰ 时间：{ts}")
    return "\n".join(lines)


def main():
    logger.info("=" * 60)
    logger.info("  NewAPI 通用签到脚本 v1.0")
    logger.info(f"  执行时间: {now_beijing().strftime('%Y-%m-%d %H:%M:%S')}")
    if DEBUG_MODE:
        logger.info("  调试模式: 已启用")
    logger.info("=" * 60)

    accounts = load_accounts()
    if not accounts:
        logger.error("无法加载账号配置，程序退出")
        sys.exit(1)

    logger.info(f"共 {len(accounts)} 个账号，开始执行签到任务")

    results = []
    for i, account in enumerate(accounts):
        result = checkin_account(account, i)
        results.append(result)

        ts = now_beijing().strftime("%Y-%m-%d %H:%M:%S")
        status = result["status"]
        name   = result["account"]

        if status == "success":
            logger.info(f"{name} 签到成功: {result['msg']}")
            tag = "签到成功"
        elif status == "fail":
            logger.warning(f"{name} 签到失败: {result['msg']}")
            tag = "签到失败"
        else:
            logger.error(f"{name} 签到出错: {result['msg']}")
            tag = "签到出错"

        safe_send_notify(f"[NewAPI]{tag}", build_notify_content(result, ts))

        if i < len(accounts) - 1:
            time.sleep(3)

    # 统计
    success = sum(1 for r in results if r["status"] == "success")
    fail    = sum(1 for r in results if r["status"] == "fail")
    error   = sum(1 for r in results if r["status"] == "error")
    total   = len(results)

    logger.info("=" * 60)
    logger.info(f"  所有账号签到完成")
    logger.info(f"  成功: {success} | 失败: {fail} | 出错: {error}")
    logger.info(f"  完成时间: {now_beijing().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # 多账号汇总通知
    if total > 1:
        ts = now_beijing().strftime("%Y-%m-%d %H:%M:%S")
        summary = (
            f"📊 签到汇总：\n"
            f"✅ 成功：{success}个\n"
            f"⚠️ 失败：{fail}个\n"
            f"❌ 出错：{error}个\n"
            f"📈 成功率：{success/total*100:.1f}%\n"
            f"⏰ 完成时间：{ts}"
        )
        safe_send_notify("[NewAPI]签到汇总", summary)

    sys.exit(0 if success > 0 else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("程序被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        sys.exit(1)
