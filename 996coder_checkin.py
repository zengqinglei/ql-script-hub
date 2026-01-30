#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 设置 Windows 控制台 UTF-8 编码（必须在最开始）
import sys
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

"""
cron "0 9 * * *" script-path=996coder_checkin.py,tag=996Coder签到
new Env('996Coder签到')

996Coder 自动签到青龙脚本
通过浏览器自动化登录完成签到(签到在登录时触发)
使用邮箱密码认证方式
"""

import asyncio
import json
import os
import random
import re
import tempfile
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 时区支持
try:
    from zoneinfo import ZoneInfo
    BEIJING_TZ = ZoneInfo("Asia/Shanghai")
except ImportError:
    BEIJING_TZ = None

# ==================== 日志类 ====================
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

# 导入 Playwright
try:
    from playwright.async_api import async_playwright, Page, BrowserContext
except ImportError:
    logger.error("未安装 Playwright，无法使用浏览器自动化")
    logger.info("安装方法：pip install playwright && playwright install chromium")
    sys.exit(1)

# 导入 httpx (异步HTTP客户端)
try:
    import httpx
except ImportError:
    logger.error("未安装 httpx，无法进行API请求")
    logger.info("安装方法：pip install httpx")
    sys.exit(1)

# 添加 notify 模块路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".github", "workflows"))

# 可选通知模块
hadsend = False
try:
    from notify import send
    hadsend = True
    logger.info("通知模块加载成功")
except Exception as e:
    logger.warning(f"通知模块加载失败: {e}")
    def send(title, content):
        pass


# ==================== 配置常量 ====================
BASE_URL = os.getenv("CODER996_BASE_URL") or "https://996coder.com"
LOGIN_URL = f"{BASE_URL}/login"
CHECKIN_URL = f"{BASE_URL}/api/user/checkin"
USER_INFO_URL = f"{BASE_URL}/api/user/self"
TIMEOUT = int(os.getenv("CODER996_TIMEOUT", "30"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# 浏览器配置
BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
BROWSER_TIMEOUT = 20000  # 20秒
PAGE_LOAD_TIMEOUT = 15000  # 15秒

# User-Agent
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# 余额转换率 (内部单位 -> 美元)
QUOTA_TO_DOLLAR_RATE = 500000

# 关键Cookie名称
KEY_COOKIE_NAMES = ["session", "sessionid", "token", "auth", "jwt"]

# WAF Cookie名称
WAF_COOKIE_NAMES = ["acw_tc", "cdn_sec_tc", "acw_sc__v2"]

# 邮箱输入框选择器
EMAIL_INPUT_SELECTORS = [
    'input[type="email"]',
    'input[name="email"]',
    'input[placeholder*="邮箱"]',
    'input[placeholder*="Email"]',
    'input[id*="email"]',
]

# 密码输入框选择器
PASSWORD_INPUT_SELECTORS = [
    'input[type="password"]',
    'input[name="password"]',
]

# 登录按钮选择器
LOGIN_BUTTON_SELECTORS = [
    'button[type="submit"]',
    'button:has-text("登录")',
    'button:has-text("Login")',
    'input[type="submit"]',
]

# 弹窗关闭选择器
POPUP_CLOSE_SELECTORS = [
    '.semi-modal-close',
    '[aria-label="Close"]',
    'button:has-text("关闭")',
    'button:has-text("我知道了")',
]


# ==================== 工具函数 ====================
def safe_send_notify(title: str, content: str) -> bool:
    """安全的通知发送"""
    if not hadsend:
        logger.info(f"通知: {title}")
        logger.info(f"   {content}")
        return False

    try:
        logger.info(f"正在推送通知: {title}")
        send(title, content)
        logger.info("通知推送成功")
        return True
    except Exception as e:
        logger.error(f"通知推送失败: {e}")
        return False


# ==================== 认证器类 ====================
class EmailAuthenticator:
    """邮箱密码认证"""

    def __init__(self, account_name: str, email: str, password: str):
        self.account_name = account_name
        self.email = email
        self.password = password

    async def _extract_user_info(self, cookies: Dict[str, str]) -> Tuple[Optional[str], Optional[str]]:
        """从用户信息API提取用户ID和用户名"""
        try:
            headers = {"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/json"}
            async with httpx.AsyncClient(cookies=cookies, timeout=10.0, verify=True) as client:
                response = await client.get(USER_INFO_URL, headers=headers)
                logger.debug(f"API 请求：访问 {USER_INFO_URL}")
                logger.debug(f"响应：状态码 {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("data"):
                        user_data = data["data"]
                        user_id = user_data.get("id") or user_data.get("user_id")
                        username = user_data.get("username") or user_data.get("name") or user_data.get("email")
                        if user_id or username:
                            logger.info(f"{self.account_name}: 提取到用户标识: ID={user_id}, 用户名={username}")
                            return str(user_id) if user_id else None, username
        except Exception as e:
            logger.warning(f"{self.account_name}: 提取用户信息失败: {e}")
        return None, None

    async def _close_popups(self, page: Page):
        """关闭可能的弹窗"""
        try:
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(300)
            for sel in POPUP_CLOSE_SELECTORS:
                try:
                    close_btn = await page.query_selector(sel)
                    if close_btn:
                        await close_btn.click()
                        await page.wait_for_timeout(300)
                        break
                except:
                    continue
        except:
            pass

    async def _find_email_input(self, page: Page):
        """查找邮箱输入框"""
        logger.info(f"{self.account_name}: 查找邮箱输入框...")
        for sel in EMAIL_INPUT_SELECTORS:
            try:
                email_input = await page.query_selector(sel)
                if email_input:
                    logger.info(f"{self.account_name}: 找到邮箱输入框: {sel}")
                    return email_input
            except:
                continue

        # 调试信息
        try:
            page_title = await page.title()
            page_url = page.url
            logger.error(f"{self.account_name}: 未找到邮箱输入框")
            logger.info(f"   当前页面: {page_title}")
            logger.info(f"   当前URL: {page_url}")

            # 查找所有输入框
            all_inputs = await page.query_selector_all('input')
            logger.info(f"   页面共有 {len(all_inputs)} 个输入框")
            for i, inp in enumerate(all_inputs[:5]):
                try:
                    inp_type = await inp.get_attribute('type')
                    inp_name = await inp.get_attribute('name')
                    inp_placeholder = await inp.get_attribute('placeholder')
                    logger.info(f"     输入框{i+1}: type={inp_type}, name={inp_name}, placeholder={inp_placeholder}")
                except:
                    logger.info(f"     输入框{i+1}: 无法获取属性")

        except Exception as e:
            logger.info(f"   调试信息获取失败: {e}")

        return None

    async def _check_login_success(self, page: Page) -> Tuple[bool, Optional[str]]:
        """检查登录是否成功"""
        current_url = page.url
        logger.info(f"{self.account_name}: 登录后URL: {current_url}")

        # 方法1: 检查URL变化
        if "login" not in current_url.lower():
            logger.info(f"{self.account_name}: URL已变化，登录可能成功")
            return True, None

        logger.warning(f"{self.account_name}: 仍在登录页面，检查其他登录指标...")

        # 方法2: 检查错误提示
        try:
            error_selectors = ['.error', '.alert-danger', '[class*="error"]', '.toast-error', '[role="alert"]']
            for sel in error_selectors:
                error_msg = await page.query_selector(sel)
                if error_msg:
                    error_text = await error_msg.inner_text()
                    if error_text and error_text.strip():
                        logger.error(f"{self.account_name}: 登录错误: {error_text}")
                        return False, f"登录失败: {error_text}"
        except:
            pass

        # 仍在登录页
        if "login" in current_url.lower():
            return False, "登录失败，仍在登录页面"

        return True, None

    async def authenticate(self, page: Page, context: BrowserContext) -> Dict:
        """使用邮箱密码登录"""
        try:
            logger.info(f"{self.account_name}: 开始邮箱密码认证")
            logger.info(f"{self.account_name}: 使用邮箱: {self.email}")

            # 步骤1: 访问登录页
            logger.info(f"{self.account_name}: 访问登录页...")
            await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
            logger.debug(f"API 请求：访问 {LOGIN_URL}")
            await page.wait_for_timeout(2000)

            # 步骤2: 关闭可能的弹窗
            await self._close_popups(page)

            # 步骤3: 点击"使用邮箱或用户名登录"按钮
            logger.info(f"{self.account_name}: 查找邮箱登录选项...")
            email_login_button = None
            for sel in [
                'button:has-text("使用 邮箱或用户名 登录")',
                'button:has-text("邮箱或用户名")',
                'button:has-text("邮箱登录")',
                'button:has-text("Email")',
            ]:
                try:
                    email_login_button = await page.query_selector(sel)
                    if email_login_button:
                        logger.info(f"{self.account_name}: 找到邮箱登录按钮: {sel}")
                        await email_login_button.click()
                        await page.wait_for_timeout(1000)
                        break
                except:
                    continue

            if not email_login_button:
                logger.warning(f"{self.account_name}: 未找到邮箱登录按钮，继续尝试查找输入框...")

            # 步骤4: 查找邮箱输入框
            email_input = await self._find_email_input(page)
            if not email_input:
                return {"success": False, "error": "未找到邮箱输入框"}

            # 步骤5: 查找密码输入框
            password_input = None
            for sel in PASSWORD_INPUT_SELECTORS:
                try:
                    password_input = await page.query_selector(sel)
                    if password_input:
                        logger.info(f"{self.account_name}: 找到密码输入框: {sel}")
                        break
                except:
                    continue

            if not password_input:
                return {"success": False, "error": "未找到密码输入框"}

            # 步骤5: 填写邮箱和密码
            logger.info(f"{self.account_name}: 填写登录表单...")
            try:
                await email_input.fill(self.email)
                await page.wait_for_timeout(500)
                await password_input.fill(self.password)
                await page.wait_for_timeout(500)
            except Exception as e:
                return {"success": False, "error": f"填写表单失败: {str(e)}"}

            # 步骤6: 查找并点击登录按钮
            login_button = None
            for sel in LOGIN_BUTTON_SELECTORS:
                try:
                    login_button = await page.query_selector(sel)
                    if login_button:
                        logger.info(f"{self.account_name}: 找到登录按钮: {sel}")
                        break
                except:
                    continue

            if not login_button:
                return {"success": False, "error": "未找到登录按钮"}

            # 步骤7: 点击登录
            logger.info(f"{self.account_name}: 点击登录按钮...")
            await login_button.click()

            # 步骤8: 等待页面跳转或响应
            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
                await page.wait_for_timeout(2000)
            except:
                logger.warning(f"{self.account_name}: 页面加载超时，继续检查登录状态...")

            # 步骤9: 检查登录是否成功
            success, error_msg = await self._check_login_success(page)
            if not success:
                return {"success": False, "error": error_msg}

            # 步骤10: 获取 cookies
            logger.info(f"{self.account_name}: 获取登录cookies...")
            final_cookies = await context.cookies()
            cookies_dict = {cookie["name"]: cookie["value"] for cookie in final_cookies}

            logger.info(f"{self.account_name}: 获取到 {len(cookies_dict)} 个 cookies")
            for name in KEY_COOKIE_NAMES:
                if name in cookies_dict:
                    logger.debug(f"   关键cookie {name}: {cookies_dict[name][:50]}...")

            # 步骤11: 提取用户信息
            user_id, user_name = await self._extract_user_info(cookies_dict)

            logger.info(f"{self.account_name}: 邮箱密码认证成功")
            return {
                "success": True,
                "cookies": cookies_dict,
                "user_id": user_id,
                "username": user_name
            }

        except Exception as e:
            return {"success": False, "error": f"邮箱密码认证失败: {str(e)}"}


# ==================== 签到管理类 ====================
class AgentRouterCheckIn:
    """996Coder 签到管理"""

    def __init__(self, account_config: Dict, account_index: int):
        self.account_config = account_config
        self.account_index = account_index
        self.account_name = account_config.get("name", f"账号{account_index + 1}")

    async def execute(self) -> Dict:
        """执行签到"""
        logger.info(f"\n{'='*60}")
        logger.info(f"{self.account_name}: 开始签到")
        logger.info(f"{'='*60}")

        # 检查邮箱密码认证配置
        email = self.account_config.get("email")
        password = self.account_config.get("password")

        if not email or not password:
            return {
                "success": False,
                "account": self.account_name,
                "error": "未配置邮箱或密码"
            }

        # 执行邮箱密码认证签到
        logger.info(f"\n{self.account_name}: 尝试邮箱密码认证...")

        async with async_playwright() as playwright:
            try:
                result = await self._checkin_with_auth(playwright, "email", email, password)
                return result
            except Exception as e:
                logger.error(f"{self.account_name}: 邮箱密码认证异常: {str(e)}")
                return {
                    "success": False,
                    "account": self.account_name,
                    "error": f"邮箱密码认证异常: {str(e)}"
                }

    async def _checkin_with_auth(self, playwright, auth_type: str, email: str, password: str) -> Dict:
        """使用指定认证方式签到"""
        logger.info(f"{self.account_name}: 开始使用 {auth_type} 认证签到流程...")

        effective_headless = BROWSER_HEADLESS

        # 从 Regular-inspection 项目借鉴的高级反检测技术
        # 针对低配Docker环境（CPU<1核，内存<1GB）优化
        browser_launch_args = [
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
            "--window-size=1280,720",  # 降低分辨率减少渲染压力
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-site-isolation-trials",
            "--disable-features=BlockInsecurePrivateNetworkRequests",
            # 低配环境优化参数（移除--single-process避免崩溃）
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

        # 更全面的Stealth脚本
        stealth_script = """
            // 1. 隐藏webdriver特征
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined,
            });

            // 2. 修复语言特征
            Object.defineProperty(navigator, 'languages', {
              get: () => ['zh-CN', 'zh', 'en-US', 'en'],
            });

            // 3. 修复权限查询
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
              parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );

            // 4. 伪装plugins
            Object.defineProperty(navigator, 'plugins', {
              get: () => [
                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
              ],
            });

            // 5. 修复WebGL指纹
            try {
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) { // UNMASKED_VENDOR_WEBGL
                        return 'Intel Inc.';
                    }
                    if (parameter === 37446) { // UNMASKED_RENDERER_WEBGL
                        return 'Intel Iris OpenGL Engine';
                    }
                    return getParameter.call(this, parameter);
                };
            } catch (e) {}

            // 6. 修复chrome对象（重要！）
            if (!window.chrome) {
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
            }

            // 7. 隐藏headless特征
            Object.defineProperty(navigator, 'maxTouchPoints', {
                get: () => 1,
            });

            // 8. 修复navigator.platform
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32',
            });

            // 9. 修复deviceMemory
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8,
            });

            // 10. 修复hardwareConcurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8,
            });
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            # 启动浏览器
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=temp_dir,
                headless=effective_headless,
                user_agent=DEFAULT_USER_AGENT,
                viewport={"width": 1920, "height": 1080},
                args=browser_launch_args,
                java_script_enabled=True,
            )

            page = await context.new_page()

            # 注入stealth脚本
            await page.add_init_script(stealth_script)
            logger.info(f"{self.account_name}: 已注入高级Stealth脚本以增强反检测能力")

            # 用于捕获签到信息和用户余额
            checkin_info = {"found": False, "message": "", "reward": ""}
            user_balance_info = {"quota": 0, "used_quota": 0, "username": "", "user_id": ""}

            # 监听所有网络响应，捕获签到和余额信息
            async def handle_response(response):
                try:
                    url = response.url
                    method = response.request.method

                    # 关注所有API请求
                    if "/api/" in url:
                        # 打印请求方法和URL
                        logger.debug(f"API 请求：{method} {url}")
                        logger.debug(f"响应：状态码 {response.status}")

                        # 尝试解析JSON响应
                        if response.status == 200:
                            try:
                                json_data = await response.json()
                                # 打印响应数据（前500字符）
                                logger.debug(f"   响应数据: {json.dumps(json_data, ensure_ascii=False)[:500]}")

                                # 检查是否包含签到相关信息
                                if isinstance(json_data, dict):
                                    # 查找签到消息
                                    message = json_data.get("message") or json_data.get("msg") or ""

                                    # 扩大关键词匹配范围
                                    if any(keyword in message.lower() for keyword in ["签到", "sign", "check", "今日", "已", "成功"]):
                                        checkin_info["found"] = True
                                        checkin_info["message"] = message
                                        logger.info(f"{self.account_name}: 捕获签到响应: {url}")
                                        logger.info(f"   消息: {message}")

                                        # 尝试提取奖励金额
                                        if "data" in json_data:
                                            data = json_data["data"]
                                            if isinstance(data, dict):
                                                # 查找可能的奖励字段
                                                for key in ["reward", "amount", "quota", "balance", "credit", "income"]:
                                                    if key in data:
                                                        checkin_info["reward"] = str(data[key])
                                                        logger.info(f"   奖励: {data[key]}")
                                                        break

                                    # 即使消息不匹配，也检查是否有签到相关的字段
                                    if "sign" in url.lower() or "checkin" in url.lower():
                                        checkin_info["found"] = True
                                        checkin_info["message"] = message or "签到成功"
                                        logger.info(f"{self.account_name}: 检测到签到API调用: {url}")

                                        if "data" in json_data and isinstance(json_data["data"], dict):
                                            data = json_data["data"]
                                            for key in ["reward", "amount", "quota", "balance", "credit", "income"]:
                                                if key in data:
                                                    checkin_info["reward"] = str(data[key])
                                                    logger.info(f"   奖励: {data[key]}")
                                                    break

                                    # 捕获登录响应中的用户余额信息
                                    if "/api/user/login" in url or "/api/user/self" in url:
                                        if json_data.get("success") and json_data.get("data"):
                                            user_data = json_data["data"]
                                            if "quota" in user_data:
                                                user_balance_info["quota"] = user_data.get("quota", 0)
                                                user_balance_info["used_quota"] = user_data.get("used_quota", 0)
                                                user_balance_info["username"] = user_data.get("display_name") or user_data.get("username", "")
                                                if "id" in user_data:
                                                    user_balance_info["user_id"] = str(user_data["id"])
                                                logger.debug(f"{self.account_name}: 捕获用户余额 - quota: {user_balance_info['quota']}, used: {user_balance_info['used_quota']}")
                            except Exception as e:
                                logger.debug(f"  JSON解析失败: {e}")
                except Exception as e:
                    logger.debug(f"  响应处理异常: {e}")

            page.on("response", handle_response)

            try:
                # 步骤1: 获取 WAF cookies
                await self._get_waf_cookies(page, context)

                # 步骤2: 执行邮箱密码认证
                authenticator = EmailAuthenticator(self.account_name, email, password)
                auth_result = await authenticator.authenticate(page, context)

                if not auth_result["success"]:
                    return {
                        "success": False,
                        "account": self.account_name,
                        "error": auth_result.get("error")
                    }

                logger.info(f"{self.account_name}: 认证成功")

                # 获取认证后的 cookies
                cookies = auth_result.get("cookies", {})

                # =================================================
                # 新增：主动执行签到逻辑
                # =================================================
                logger.info(f"{self.account_name}: 正在尝试主动签到...")
                
                # 等待获取 User ID (最多等待10秒)
                wait_count = 0
                while not user_balance_info.get("user_id") and wait_count < 10:
                    logger.info(f"{self.account_name}: 等待 User ID 获取... ({wait_count+1}/10)")
                    await asyncio.sleep(1)
                    wait_count += 1
                
                # 获取 User ID (优先使用捕获到的，其次是auth结果中的)
                current_user_id = user_balance_info.get("user_id") or auth_result.get("user_id")
                
                if current_user_id:
                    logger.info(f"{self.account_name}: 获取到 User ID: {current_user_id}")
                else:
                    logger.warning(f"{self.account_name}: 未获取到 User ID，签到可能会失败")

                # 使用 page.evaluate 在浏览器上下文中执行 fetch 请求
                try:
                    logger.info(f"{self.account_name}: 尝试在浏览器中调用签到接口: {CHECKIN_URL} (POST)")
                    
                    # 定义 fetch 执行脚本
                    fetch_script = r"""async ({url, userId}) => {
                        try {
                            const headers = {
                                'Content-Type': 'application/json',
                                'Accept': 'application/json, text/plain, */*'
                            };
                            if (userId) {
                                headers['New-Api-User'] = userId;
                            }
                            const response = await fetch(url, {
                                method: 'POST',
                                headers: headers
                            });
                            const text = await response.text();
                            return {
                                status: response.status,
                                text: text
                            };
                        } catch (e) {
                            return {
                                status: 0,
                                text: e.toString()
                            };
                        }
                    }"""

                    # 执行 POST 请求
                    checkin_result = await page.evaluate(fetch_script, {"url": CHECKIN_URL, "userId": current_user_id})
                    
                    api_status = checkin_result["status"]
                    api_text = checkin_result["text"]
                    
                    logger.info(f"{self.account_name}: 签到接口响应状态: {api_status}")
                    logger.debug(f"{self.account_name}: 签到接口响应内容: {api_text}")

                    if api_status == 200:
                        try:
                            json_res = json.loads(api_text)
                            msg = json_res.get("message") or json_res.get("msg") or ""
                            
                            # 优先判断 success 字段
                            if json_res.get("success"):
                                logger.info(f"{self.account_name}: 签到成功！")
                                checkin_info["found"] = True
                                checkin_info["message"] = msg or "签到成功"
                                
                                if "data" in json_res:
                                    data = json_res["data"]
                                    if isinstance(data, dict):
                                        # 提取 quota_awarded
                                        if "quota_awarded" in data:
                                            # 转换为美元显示 (假设除以 500000)
                                            quota_val = data["quota_awarded"]
                                            quota_usd = round(quota_val / QUOTA_TO_DOLLAR_RATE, 2)
                                            checkin_info["reward"] = f"${quota_usd} ({quota_val})"
                                            logger.info(f"{self.account_name}: 获得奖励: {checkin_info['reward']}")
                                        
                                        # 兼容其他字段
                                        for key in ["reward", "amount", "quota", "balance"]:
                                            if key in data and not checkin_info["reward"]:
                                                checkin_info["reward"] = str(data[key])
                                                break
                            else:
                                if msg:
                                    logger.info(f"{self.account_name}: 接口返回消息: {msg}")
                                    checkin_info["found"] = True
                                    checkin_info["message"] = f"接口返回: {msg}"
                        except:
                            pass
                    elif api_status == 401:
                         logger.warning(f"{self.account_name}: 签到失败(401)，可能是权限或Header缺失")
                    else:
                         logger.warning(f"{self.account_name}: 签到失败，状态码: {api_status}")

                except Exception as e:
                    logger.warning(f"{self.account_name}: 浏览器内调用签到接口失败: {e}")

                # 等待一下，确保所有网络请求都被捕获
                await page.wait_for_timeout(2000)
                # =================================================

                # 步骤3: 检查网络监听中是否捕获到签到信息
                logger.info(f"{self.account_name}: 检查签到状态...")
                checkin_msg = "登录签到完成（签到在登录时自动触发）"

                if checkin_info["found"]:
                    logger.info(f"{self.account_name}: 检测到签到响应")
                    checkin_msg = checkin_info["message"]
                    if checkin_info["reward"]:
                        checkin_msg += f" | 奖励: {checkin_info['reward']}"
                else:
                    logger.info(f"{self.account_name}: {checkin_msg}")

                # AgentRouter的签到机制说明：
                # - 登录时自动完成签到，无需调用额外API
                # - 用户余额信息从登录响应中获取

                # 计算余额（转换为美元）
                quota_dollar = round(user_balance_info["quota"] / QUOTA_TO_DOLLAR_RATE, 2)
                used_dollar = round(user_balance_info["used_quota"] / QUOTA_TO_DOLLAR_RATE, 2)

                # 构建用户信息
                user_info = {
                    "success": True,
                    "quota": quota_dollar,
                    "used": used_dollar,
                    "display": f"余额: ${quota_dollar:.2f}, 已用: ${used_dollar:.2f}"
                }

                # 使用捕获的用户名（如果有）
                username = user_balance_info.get("username") or auth_result.get("username")

                logger.info(f"{self.account_name}: 签到流程完成，结果：成功")
                if quota_dollar > 0 or used_dollar > 0:
                    logger.info(f"{self.account_name}: {user_info['display']}")

                return {
                    "success": True,
                    "account": self.account_name,
                    "auth_method": auth_type,
                    "user_info": user_info,
                    "username": username,
                    "message": checkin_msg,
                    "checkin_reward": checkin_info.get("reward", "")
                }

            finally:
                await page.close()
                await context.close()

    async def _get_waf_cookies(self, page: Page, context: BrowserContext):
        """获取 WAF cookies"""
        try:
            logger.info(f"{self.account_name}: 获取 WAF cookies...")
            await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT)
            logger.debug(f"API 请求：访问 {LOGIN_URL}")
            await page.wait_for_timeout(2000)

            cookies = await context.cookies()
            waf_cookies = [c for c in cookies if c["name"] in WAF_COOKIE_NAMES]

            if waf_cookies:
                logger.info(f"{self.account_name}: 获取到 {len(waf_cookies)} 个 WAF cookies")
            else:
                logger.warning(f"{self.account_name}: 未获取到 WAF cookies")
        except Exception as e:
            logger.warning(f"{self.account_name}: 获取 WAF cookies 失败: {e}")



# ==================== 主函数 ====================
def load_accounts() -> Optional[List[Dict]]:
    """加载账号配置"""
    logger.info("开始加载账号配置...")

    accounts_str = os.getenv("CODER996_ACCOUNTS")
    if not accounts_str:
        logger.error("未设置 CODER996_ACCOUNTS 环境变量")
        return None

    try:
        accounts = json.loads(accounts_str)
        if not isinstance(accounts, list):
            logger.error("CODER996_ACCOUNTS 格式错误，应为 JSON 数组")
            return None

        logger.info(f"成功加载 {len(accounts)} 个账号配置")
        return accounts
    except Exception as e:
        logger.error(f"解析 CODER996_ACCOUNTS 失败: {e}")
        return None


async def main_async():
    """异步主函数"""
    logger.info("="*80)
    logger.info("996Coder 自动签到脚本 (重构版)")
    logger.info(f"执行时间: {now_beijing().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"基础URL: {BASE_URL}")
    logger.info(f"浏览器模式: {'无头' if BROWSER_HEADLESS else '有头'}")
    logger.info("="*80)

    # 加载账号
    accounts = load_accounts()
    if not accounts:
        logger.error("无法加载账号配置")
        return 1

    logger.info(f"\n找到 {len(accounts)} 个账号配置\n")

    # 执行签到
    results = []
    for i, account in enumerate(accounts):
        try:
            checkin = AgentRouterCheckIn(account, i)
            result = await checkin.execute()
            results.append(result)
        except Exception as e:
            logger.error(f"账号 {i+1} 处理异常: {e}")
            results.append({
                "success": False,
                "account": account.get("name", f"账号{i+1}"),
                "error": str(e)
            })

        # 账号间延迟
        if i < len(accounts) - 1:
            await asyncio.sleep(3)

    # 统计结果
    success_count = sum(1 for r in results if r.get("success"))
    total_count = len(results)

    logger.info(f"\n{'='*80}")
    logger.info("签到结果统计")
    logger.info(f"{ '='*80}")
    logger.info(f"成功: {success_count}/{total_count}")
    logger.info(f"失败: {total_count - success_count}/{total_count}")

    # 构建通知内容
    notification_lines = []
    notification_lines.append(f"🌐 域名：{BASE_URL.replace('https://', '').replace('http://', '')}")
    notification_lines.append("")

    for result in results:
        account_name = result.get("account", "未知账号")
        if result.get("success"):
            user_info = result.get("user_info")
            username = result.get("username", "")
            notification_lines.append(f"👤 {account_name}：")
            if username:
                notification_lines.append(f"📱 用户：{username}")
            notification_lines.append(f"📝 签到：{result.get('message', '签到成功')}")
            notification_lines.append(f"🔐 认证：{result.get('auth_method')}")
            if user_info and user_info.get("display"):
                notification_lines.append(f"💰 账户：{user_info['display']}")
            notification_lines.append("")
        else:
            error = result.get("error", "未知错误")
            notification_lines.append(f"👤 {account_name}：")
            notification_lines.append(f"📝 签到：签到失败 - {error}")
            notification_lines.append("")

    notification_lines.append(f"📊 统计：成功 {success_count}/{total_count}")
    notification_lines.append(f"⏰ 时间：{now_beijing().strftime('%Y-%m-%d %H:%M:%S')}")

    notification_content = "\n".join(notification_lines)

    logger.info(f"\n{notification_content}\n")

    # 发送通知
    if total_count > 0:
        title = f"[996Coder]签到{'成功' if success_count == total_count else '失败'}"
        safe_send_notify(title, notification_content)

    logger.info(f"{ '='*80}\n")

    return 0 if success_count > 0 else 1


def main():
    """同步主函数入口"""
    try:
        return asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.warning("\n程序被用户中断")
        return 1
    except Exception as e:
        logger.error(f"\n程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
