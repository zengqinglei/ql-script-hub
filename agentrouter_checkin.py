#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 设置 Windows 控制台 UTF-8 编码（必须在最开始）
import sys
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

"""
cron "0 9 * * *" script-path=agentrouter_checkin.py,tag=AgentRouter签到
new Env('AgentRouter签到')

AgentRouter 自动签到青龙脚本 - 重构版
通过浏览器自动化登录完成签到(签到在登录时触发)
支持: cookies、邮箱、GitHub、Linux.do 四种认证方式
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

# 导入 Playwright
try:
    from playwright.async_api import async_playwright, Page, BrowserContext
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    print("❌ 未安装 Playwright，无法使用浏览器自动化")
    print("   安装方法：pip install playwright && playwright install chromium")
    sys.exit(1)

# 导入 httpx (异步HTTP客户端)
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    print("❌ 未安装 httpx，无法进行API请求")
    print("   安装方法：pip install httpx")
    sys.exit(1)

# 可选通知模块
hadsend = False
try:
    from notify import send
    hadsend = True
    print("✅ 通知模块加载成功")
except Exception as e:
    print(f"⚠️ 通知模块加载失败: {e}")
    def send(title, content):
        pass


# ==================== 配置常量 ====================
BASE_URL = os.getenv("AGENTROUTER_BASE_URL", "https://agentrouter.org")
LOGIN_URL = f"{BASE_URL}/login"
CHECKIN_URL = f"{BASE_URL}/api/user/sign_in"
USER_INFO_URL = f"{BASE_URL}/api/user/self"
TIMEOUT = int(os.getenv("AGENTROUTER_TIMEOUT", "30"))
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
    'input[name="username"]',
    'input[name="account"]',
    'input[id*="email" i]',
    'input[placeholder*="邮箱" i]',
    'input[placeholder*="Email" i]',
]

# 登录按钮选择器
LOGIN_BUTTON_SELECTORS = [
    'button[type="submit"]',
    'button:has-text("登录")',
    'button:has-text("Login")',
]

# GitHub 登录按钮选择器
GITHUB_BUTTON_SELECTORS = [
    'button:has-text("GitHub")',
    'a:has-text("GitHub")',
    'text=使用 GitHub',
    'a[href*="github.com"]',
]

# Linux.do 登录按钮选择器
LINUXDO_BUTTON_SELECTORS = [
    'button:has-text("LinuxDO")',
    'a:has-text("LinuxDO")',
    'button:has-text("Linux.do")',
    'a:has-text("Linux")',
    'a[href*="linux.do"]',
]


# ==================== 工具函数 ====================
def safe_send_notify(title: str, content: str) -> bool:
    """安全的通知发送"""
    if not hadsend:
        print(f"📢 [通知] {title}")
        print(f"   {content}")
        return False

    try:
        print(f"📤 正在推送通知: {title}")
        send(title, content)
        print("✅ 通知推送成功")
        return True
    except Exception as e:
        print(f"❌ 通知推送失败: {e}")
        return False


def get_domain(url: str) -> str:
    """从 URL 提取域名"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return parsed.netloc


# ==================== 认证器类 ====================
class BaseAuthenticator:
    """认证器基类"""

    def __init__(self, account_name: str, auth_config: Dict):
        self.account_name = account_name
        self.auth_config = auth_config

    async def authenticate(self, page: Page, context: BrowserContext) -> Dict:
        """
        执行认证

        Returns:
            {
                "success": bool,
                "cookies": dict,
                "user_id": str,
                "username": str,
                "error": str
            }
        """
        raise NotImplementedError

    async def _extract_user_info(self, cookies: Dict[str, str]) -> Tuple[Optional[str], Optional[str]]:
        """从用户信息API提取用户ID和用户名"""
        try:
            headers = {"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/json"}
            async with httpx.AsyncClient(cookies=cookies, timeout=10.0, verify=True) as client:
                response = await client.get(USER_INFO_URL, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("data"):
                        user_data = data["data"]
                        user_id = user_data.get("id") or user_data.get("user_id")
                        username = user_data.get("username") or user_data.get("name") or user_data.get("email")
                        if user_id or username:
                            print(f"✅ [{self.account_name}] 提取到用户标识: ID={user_id}, 用户名={username}")
                            return str(user_id) if user_id else None, username
        except Exception as e:
            print(f"⚠️ [{self.account_name}] 提取用户信息失败: {e}")
        return None, None


class CookiesAuthenticator(BaseAuthenticator):
    """Cookies 认证"""

    async def authenticate(self, page: Page, context: BrowserContext) -> Dict:
        try:
            print(f"🍪 [{self.account_name}] 使用 Cookies 认证...")

            cookies = self.auth_config.get("cookies", {})
            if not cookies:
                return {"success": False, "error": "未提供 cookies"}

            # 转换为 Playwright 格式
            cookie_list = []
            for name, value in cookies.items():
                cookie_list.append({
                    "name": name,
                    "value": value,
                    "domain": get_domain(BASE_URL),
                    "path": "/"
                })

            await context.add_cookies(cookie_list)

            # 验证 cookies
            await page.goto(USER_INFO_URL, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
            await page.wait_for_timeout(1000)

            # 检查是否跳转到登录页
            if "login" in page.url.lower():
                return {"success": False, "error": "Cookies 已过期"}

            # 获取最新 cookies
            final_cookies = await context.cookies()
            cookies_dict = {cookie["name"]: cookie["value"] for cookie in final_cookies}

            # 提取用户信息
            user_id, username = await self._extract_user_info(cookies_dict)

            print(f"✅ [{self.account_name}] Cookies 认证成功")
            return {
                "success": True,
                "cookies": cookies_dict,
                "user_id": user_id,
                "username": username
            }

        except Exception as e:
            return {"success": False, "error": f"Cookies 认证失败: {str(e)}"}


class EmailAuthenticator(BaseAuthenticator):
    """邮箱密码认证"""

    async def authenticate(self, page: Page, context: BrowserContext) -> Dict:
        try:
            email = self.auth_config.get("email")
            password = self.auth_config.get("password")

            if not email or not password:
                return {"success": False, "error": "未提供邮箱或密码"}

            print(f"📧 [{self.account_name}] 使用邮箱认证: {email}")

            # 访问登录页
            await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
            await page.wait_for_timeout(1500)

            # 关闭可能的弹窗
            await self._close_popups(page)

            # 点击邮箱登录选项
            await self._find_and_click_email_tab(page)
            await page.wait_for_timeout(1000)

            # 查找邮箱输入框
            email_input = None
            for selector in EMAIL_INPUT_SELECTORS:
                try:
                    email_input = await page.query_selector(selector)
                    if email_input:
                        print(f"✅ [{self.account_name}] 找到邮箱输入框: {selector}")
                        break
                except:
                    continue

            if not email_input:
                return {"success": False, "error": "未找到邮箱输入框"}

            # 查找密码输入框
            password_input = await page.query_selector('input[type="password"]')
            if not password_input:
                return {"success": False, "error": "未找到密码输入框"}

            # 填写表单
            await email_input.fill(email)
            await password_input.fill(password)

            # 查找并点击登录按钮
            login_button = None
            for selector in LOGIN_BUTTON_SELECTORS:
                try:
                    login_button = await page.query_selector(selector)
                    if login_button:
                        break
                except:
                    continue

            if not login_button:
                return {"success": False, "error": "未找到登录按钮"}

            print(f"🔑 [{self.account_name}] 点击登录按钮...")
            await login_button.click()

            # 等待登录完成
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
                await page.wait_for_timeout(2000)
            except:
                print(f"⚠️ [{self.account_name}] 页面加载超时，继续检查...")

            # 检查登录结果
            success, error_msg = await self._check_login_success(page)
            if not success:
                return {"success": False, "error": error_msg}

            # 获取 cookies
            final_cookies = await context.cookies()
            cookies_dict = {cookie["name"]: cookie["value"] for cookie in final_cookies}

            # 提取用户信息
            user_id, username = await self._extract_user_info(cookies_dict)

            print(f"✅ [{self.account_name}] 邮箱认证成功")
            return {
                "success": True,
                "cookies": cookies_dict,
                "user_id": user_id,
                "username": username
            }

        except Exception as e:
            return {"success": False, "error": f"邮箱认证失败: {str(e)}"}

    async def _close_popups(self, page: Page):
        """关闭可能的弹窗"""
        try:
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(300)
        except:
            pass

    async def _find_and_click_email_tab(self, page: Page):
        """查找并点击邮箱登录选项"""
        for selector in ['button:has-text("邮箱")', 'a:has-text("邮箱")', 'button:has-text("Email")']:
            try:
                element = await page.query_selector(selector)
                if element:
                    await element.click()
                    return True
            except:
                continue
        return False

    async def _check_login_success(self, page: Page) -> Tuple[bool, Optional[str]]:
        """检查登录是否成功"""
        current_url = page.url

        # URL 变化检查
        if "login" not in current_url.lower():
            return True, None

        # 检查错误提示
        error_selectors = ['.error', '.alert-danger', '[class*="error"]']
        for selector in error_selectors:
            try:
                error_element = await page.query_selector(selector)
                if error_element:
                    error_text = await error_element.inner_text()
                    if error_text and ("失败" in error_text.lower() or "error" in error_text.lower()):
                        return False, f"登录失败: {error_text}"
            except:
                pass

        # 仍在登录页
        if "login" in current_url.lower():
            return False, "登录失败 - 仍在登录页面"

        return True, None


class GitHubAuthenticator(BaseAuthenticator):
    """GitHub OAuth 认证"""

    async def authenticate(self, page: Page, context: BrowserContext) -> Dict:
        try:
            username = self.auth_config.get("username")
            password = self.auth_config.get("password")

            if not username or not password:
                return {"success": False, "error": "未提供用户名或密码"}

            print(f"🐙 [{self.account_name}] 使用 GitHub 认证: {username}")

            # 访问登录页
            await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
            await page.wait_for_timeout(1500)

            # 查找 GitHub 登录按钮
            github_button = None
            for selector in GITHUB_BUTTON_SELECTORS:
                try:
                    github_button = await page.query_selector(selector)
                    if github_button:
                        print(f"✅ [{self.account_name}] 找到 GitHub 登录按钮: {selector}")
                        break
                except:
                    continue

            if not github_button:
                return {"success": False, "error": "未找到 GitHub 登录按钮"}

            await github_button.click()
            await page.wait_for_load_state("networkidle", timeout=15000)

            # 如果跳转到 GitHub
            if "github.com" in page.url:
                # 填写登录表单
                username_input = await page.query_selector('input[name="login"]')
                password_input = await page.query_selector('input[name="password"]')

                if username_input and password_input:
                    await username_input.fill(username)
                    await password_input.fill(password)

                    # 提交登录
                    submit_button = await page.query_selector('input[type="submit"]')
                    if submit_button:
                        await submit_button.click()
                        await page.wait_for_load_state("networkidle", timeout=15000)

                # 点击授权按钮（如果有）
                authorize_button = await page.query_selector('button[name="authorize"]')
                if authorize_button:
                    await authorize_button.click()
                    await page.wait_for_load_state("networkidle", timeout=10000)

            # 等待回调
            target_pattern = re.compile(rf"^{re.escape(BASE_URL)}.*")
            await page.wait_for_url(target_pattern, timeout=20000)

            # 获取 cookies
            final_cookies = await context.cookies()
            cookies_dict = {cookie["name"]: cookie["value"] for cookie in final_cookies}

            # 提取用户信息
            user_id, user_name = await self._extract_user_info(cookies_dict)

            print(f"✅ [{self.account_name}] GitHub 认证成功")
            return {
                "success": True,
                "cookies": cookies_dict,
                "user_id": user_id,
                "username": user_name
            }

        except Exception as e:
            return {"success": False, "error": f"GitHub 认证失败: {str(e)}"}


class LinuxDoAuthenticator(BaseAuthenticator):
    """Linux.do OAuth 认证"""

    async def authenticate(self, page: Page, context: BrowserContext) -> Dict:
        try:
            username = self.auth_config.get("username")
            password = self.auth_config.get("password")

            if not username or not password:
                return {"success": False, "error": "未提供用户名或密码"}

            print(f"🐧 [{self.account_name}] 使用 Linux.do 认证: {username}")

            # 步骤1: 访问登录页
            print(f"🌐 [{self.account_name}] 访问登录页...")
            await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
            await page.wait_for_timeout(1500)

            # 关闭可能的弹窗
            try:
                await page.keyboard.press('Escape')
                await page.wait_for_timeout(300)
            except:
                pass

            # 步骤2: 查找并点击"使用LinuxDO继续"按钮
            print(f"🔍 [{self.account_name}] 查找 LinuxDO 登录按钮...")
            linux_button = None
            for selector in LINUXDO_BUTTON_SELECTORS:
                try:
                    linux_button = await page.query_selector(selector)
                    if linux_button:
                        print(f"✅ [{self.account_name}] 找到 LinuxDO 登录按钮: {selector}")
                        break
                except:
                    continue

            if not linux_button:
                return {"success": False, "error": "未找到 LinuxDO 登录按钮"}

            # 点击LinuxDO登录按钮（会打开popup窗口）
            print(f"🖱️ [{self.account_name}] 点击'使用LinuxDO继续'按钮...")

            # 关键：监听popup窗口
            async with page.expect_popup() as popup_info:
                await linux_button.click()

            # 获取popup窗口
            popup_page = await popup_info.value
            print(f"🆕 [{self.account_name}] 检测到popup窗口: {popup_page.url}")
            await popup_page.wait_for_timeout(2000)

            # 步骤3: 等待popup页面完全加载并跳转
            try:
                await popup_page.wait_for_load_state("domcontentloaded", timeout=10000)
                await popup_page.wait_for_timeout(3000)  # 额外等待，确保重定向完成
            except:
                print(f"⚠️ [{self.account_name}] Popup页面加载超时，继续执行...")

            current_url = popup_page.url
            print(f"🔗 [{self.account_name}] Popup加载后URL: {current_url}")

            # 如果URL中包含 oauth2/authorize，说明已经在授权页面
            if "/oauth2/authorize" in current_url or "/authorize" in current_url:
                print(f"✅ [{self.account_name}] 检测到OAuth授权页面")
            elif "/login" in current_url:
                # 等待可能的跳转到授权页面
                print(f"⏳ [{self.account_name}] 当前在登录页，等待跳转...")
                await popup_page.wait_for_timeout(3000)
                current_url = popup_page.url
                print(f"🔗 [{self.account_name}] 等待后URL: {current_url}")

            # 步骤4: 如果跳转到Linux.do登录页，在popup中填写登录表单
            if "linux.do" in current_url and "/login" in current_url:
                print(f"🌐 [{self.account_name}] 检测到Linux.do登录页，填写登录表单...")
                await popup_page.wait_for_timeout(1000)

                # 查找登录表单
                username_input = await popup_page.query_selector('input[id="login-account-name"]')
                password_input = await popup_page.query_selector('input[id="login-account-password"]')

                if username_input and password_input:
                    print(f"✅ [{self.account_name}] 找到登录表单")

                    # 模拟人类行为：先聚焦，然后逐字输入
                    # 输入用户名（模拟真实打字）
                    await username_input.click()
                    await popup_page.wait_for_timeout(random.randint(300, 600))
                    await username_input.type(username, delay=random.randint(50, 150))

                    # 随机延迟后输入密码
                    await popup_page.wait_for_timeout(random.randint(500, 1000))
                    await password_input.click()
                    await popup_page.wait_for_timeout(random.randint(200, 400))
                    await password_input.type(password, delay=random.randint(50, 150))

                    # 输入完成后随机等待（模拟人类思考）
                    await popup_page.wait_for_timeout(random.randint(800, 1500))

                    # 点击登录按钮
                    login_button = await popup_page.query_selector('button[id="login-button"]')
                    if login_button:
                        print(f"🔑 [{self.account_name}] 点击登录按钮...")
                        await login_button.click()

                        # --- 开始重构的智能等待逻辑 ---
                        print(f"⏳ [{self.account_name}] 等待登录后跳转或Cloudflare验证...")

                        start_time = time.time()
                        login_success = False
                        last_log_time = 0

                        while time.time() - start_time < 45:  # 45秒总超时
                            # 1. 检查是否成功导航
                            if "/login" not in popup_page.url:
                                print(f"✅ [{self.account_name}] 登录成功，已跳转: {popup_page.url}")
                                login_success = True
                                break

                            # 2. 检查并处理Cloudflare Turnstile
                            try:
                                cf_iframe_locator = popup_page.frame_locator('iframe[src*="challenges.cloudflare.com"]')
                                if await cf_iframe_locator.is_visible(timeout=1000):
                                    print(f"🤖 [{self.account_name}] 检测到Cloudflare验证，尝试处理...")
                                    checkbox = cf_iframe_locator.locator('input[type="checkbox"]')
                                    if await checkbox.is_visible(timeout=2000):
                                        await checkbox.click(timeout=5000, force=True)
                                        print(f"✅ [{self.account_name}] Cloudflare复选框点击成功。")
                                    else:
                                        # 如果没有复选框，尝试点击iframe的body
                                        await cf_iframe_locator.locator('body').click(timeout=5000, force=True)
                                        print(f"✅ [{self.account_name}] Cloudflare iframe body点击成功。")
                                    
                                    print(f"⏳ [{self.account_name}] Cloudflare处理完毕，等待页面响应...")
                                    await popup_page.wait_for_timeout(3000)  # 等待验证结果
                                    continue  # 继续循环，检查是否已跳转
                            except Exception:
                                # 忽略查找iframe的超时错误，因为它可能尚未出现
                                pass

                            # 3. 检查错误提示
                            try:
                                error_el = await popup_page.query_selector('.alert-error, #modal-alert, .error, [role="alert"]')
                                if error_el and await error_el.is_visible(timeout=500):
                                    error_text = await error_el.inner_text()
                                    if error_text and error_text.strip():
                                        print(f"❌ [{self.account_name}] 检测到登录错误: {error_text.strip()}")
                                        return {"success": False, "error": f"登录失败: {error_text.strip()}"}
                            except Exception:
                                pass

                            # 4. 定期打印等待状态
                            elapsed = int(time.time() - start_time)
                            if elapsed > 3 and elapsed - last_log_time >= 5:
                                last_log_time = elapsed
                                try:
                                    login_btn_check = await popup_page.query_selector('button.is-loading')
                                    if login_btn_check:
                                        print(f"   登录按钮仍在加载中... ({elapsed}s)")
                                    else:
                                        print(f"   等待跳转中... ({elapsed}s)")
                                except Exception:
                                    print(f"   等待页面响应... ({elapsed}s)")

                            await popup_page.wait_for_timeout(1000)  # 轮询间隔

                        if not login_success:
                            print(f"⚠️ [{self.account_name}] 登录超时（45秒），页面可能卡住。")
                            try:
                                login_btn_final = await popup_page.query_selector('button[id="login-button"]')
                                if login_btn_final:
                                    btn_text = await login_btn_final.inner_text()
                                    btn_class = await login_btn_final.get_attribute('class')
                                    print(f"   最终按钮状态: '{btn_text.strip()}' | class='{btn_class}'")
                            except:
                                pass
                            return {"success": False, "error": "登录超时，未能跳转或完成验证"}

                        print(f"✅ [{self.account_name}] Linux.do 登录流程完成")

                        # 等待授权确认页面加载
                        print(f"⏳ [{self.account_name}] 等待授权确认页面加载...")
                        await popup_page.wait_for_timeout(2000)


                    else:
                        return {"success": False, "error": "未找到 Linux.do 登录按钮"}
                else:
                    return {"success": False, "error": "未找到 Linux.do 登录表单"}

            # 步骤5: 等待跳转到OAuth授权确认页面
            current_url = popup_page.url
            print(f"🔗 [{self.account_name}] 步骤5 - 当前URL: {current_url}")

            # 如果当前不是授权页面，等待跳转到授权页面
            if "authorize" not in current_url and "/oauth2/" not in current_url:
                print(f"⏳ [{self.account_name}] 等待跳转到OAuth授权页面...")

                # 等待URL跳转到授权页面（最多15秒）
                for i in range(15):
                    await popup_page.wait_for_timeout(1000)
                    current_url = popup_page.url

                    if "authorize" in current_url or "/oauth2/" in current_url:
                        print(f"✅ [{self.account_name}] 已跳转到OAuth授权页面: {current_url}")
                        break

                    if (i + 1) % 5 == 0:
                        print(f"   等待授权页面... ({i+1}s) - 当前: {current_url[:80]}...")
                else:
                    print(f"⚠️ [{self.account_name}] 未跳转到授权页面，当前URL: {current_url}")

            # 步骤6: 处理OAuth授权确认页面（在popup中）
            current_url = popup_page.url
            print(f"🔗 [{self.account_name}] 准备处理授权页面: {current_url}")

            if "linux.do" in current_url or "authorize" in current_url:
                print(f"🔍 [{self.account_name}] 等待OAuth授权页面加载完成...")

                # 等待页面完全加载
                try:
                    await popup_page.wait_for_load_state("networkidle", timeout=10000)
                    await popup_page.wait_for_timeout(2000)
                except:
                    print(f"⚠️ [{self.account_name}] 页面加载超时，继续执行...")

                # 先处理OAuth授权页面的Cloudflare验证（可能会出现）
                print(f"🔍 [{self.account_name}] 检查OAuth授权页面是否需要Cloudflare验证...")
                try:
                    await popup_page.wait_for_timeout(1000)

                    # 查找Cloudflare Turnstile iframe
                    cf_handled_auth = False
                    for attempt in range(3):
                        try:
                            frames = popup_page.frames
                            cf_frame = None
                            for frame in frames:
                                frame_url = frame.url
                                if 'cloudflare' in frame_url or 'turnstile' in frame_url or 'challenges' in frame_url:
                                    cf_frame = frame
                                    print(f"✅ [{self.account_name}] OAuth页面发现Cloudflare验证 (尝试{attempt+1}/3)")
                                    break

                            if cf_frame:
                                print(f"🤖 [{self.account_name}] 点击OAuth页面的Cloudflare验证...")
                                try:
                                    checkbox = await cf_frame.query_selector('input[type="checkbox"], body')
                                    if checkbox:
                                        await checkbox.click(timeout=3000)
                                        print(f"✅ [{self.account_name}] Cloudflare验证点击成功")
                                        cf_handled_auth = True
                                        break
                                except Exception as e:
                                    print(f"⚠️ [{self.account_name}] Cloudflare验证点击失败 (尝试{attempt+1}): {e}")
                                    if attempt < 2:
                                        await popup_page.wait_for_timeout(500)
                            else:
                                break
                        except Exception as e:
                            if attempt < 2:
                                await popup_page.wait_for_timeout(500)

                    if cf_handled_auth:
                        # 等待验证完成并且"允许"按钮出现
                        print(f"⏳ [{self.account_name}] 等待Cloudflare验证完成，授权按钮应该会出现...")
                        await popup_page.wait_for_timeout(3000)
                        try:
                            await popup_page.wait_for_load_state("networkidle", timeout=10000)
                        except:
                            pass
                    else:
                        print(f"ℹ️ [{self.account_name}] OAuth页面无需Cloudflare验证")

                except Exception as e:
                    print(f"⚠️ [{self.account_name}] OAuth页面Cloudflare检查失败: {e}")

                # 查找并点击"允许"按钮
                print(f"🔍 [{self.account_name}] 查找授权确认按钮...")
                authorize_button = None

                try:
                    # 方法1: 直接通过文本内容查找（最可靠）
                    print(f"   尝试通过文本查找'允许'按钮...")
                    authorize_button = await popup_page.query_selector('text="允许"')

                    if not authorize_button:
                        # 方法2: 查找所有按钮，遍历找到包含"允许"的
                        print(f"   尝试遍历所有按钮...")
                        all_buttons = await popup_page.query_selector_all('button')
                        for btn in all_buttons:
                            btn_text = await btn.inner_text()
                            if "允许" in btn_text or "授权" in btn_text or "Authorize" in btn_text or "Allow" in btn_text:
                                authorize_button = btn
                                print(f"✅ [{self.account_name}] 找到授权按钮: '{btn_text.strip()}'")
                                break

                    if authorize_button:
                        is_visible = await authorize_button.is_visible()
                        if is_visible:
                            print(f"🔐 [{self.account_name}] 点击'允许'按钮...")
                            await authorize_button.click()
                            await popup_page.wait_for_timeout(2000)
                            print(f"✅ [{self.account_name}] OAuth授权确认完成")
                        else:
                            print(f"⚠️ [{self.account_name}] 找到按钮但不可见")
                            authorize_button = None
                    else:
                        print(f"⚠️ [{self.account_name}] 未找到授权按钮")

                except Exception as e:
                    print(f"⚠️ [{self.account_name}] 查找授权按钮异常: {e}")
                    authorize_button = None

                if not authorize_button:
                    # 调试：保存页面截图和HTML
                    try:
                        screenshot_path = f"authorize_page_{self.account_name}.png"
                        await popup_page.screenshot(path=screenshot_path)
                        print(f"📸 [{self.account_name}] 已保存授权页面截图: {screenshot_path}")

                        # 保存HTML用于调试
                        html_content = await popup_page.content()
                        html_path = f"authorize_page_{self.account_name}.html"
                        with open(html_path, 'w', encoding='utf-8') as f:
                            f.write(html_content)
                        print(f"📄 [{self.account_name}] 已保存授权页面HTML: {html_path}")
                    except:
                        pass
                    print(f"⚠️ [{self.account_name}] 可能已自动授权，继续等待回调...")

            # 步骤7: 切换回原窗口，等待回调到AgentRouter
            print(f"🔄 [{self.account_name}] 切换回原窗口，等待OAuth回调...")
            try:
                # 在原窗口等待回调到 agentrouter.org
                target_pattern = re.compile(rf"^{re.escape(BASE_URL)}.*")
                await page.wait_for_url(target_pattern, timeout=25000)

                callback_url = page.url
                print(f"✅ [{self.account_name}] OAuth回调成功: {callback_url}")

                # 检查回调URL
                if "/console/token" in callback_url:
                    print(f"🎯 [{self.account_name}] 完美！回调到签到页面: /console/token")
                elif "/console" in callback_url:
                    print(f"✅ [{self.account_name}] 回调到控制台页面: {callback_url}")
                else:
                    print(f"⚠️ [{self.account_name}] 回调URL不是预期的: {callback_url}")

                # 等待页面完全加载（签到在此时自动触发）
                print(f"⏳ [{self.account_name}] 等待页面加载完成（签到会自动触发）...")
                await page.wait_for_load_state("networkidle", timeout=20000)
                await page.wait_for_timeout(3000)
                print(f"✅ [{self.account_name}] 页面加载完成，签到已自动完成")

            except Exception as e:
                print(f"❌ [{self.account_name}] 等待OAuth回调失败: {e}")
                print(f"   原窗口URL: {page.url}")
                print(f"   Popup窗口URL: {popup_page.url}")
                return {"success": False, "error": f"OAuth回调超时: {str(e)}"}
            finally:
                # 关闭popup窗口
                try:
                    if not popup_page.is_closed():
                        await popup_page.close()
                        print(f"🗑️ [{self.account_name}] 已关闭popup窗口")
                except:
                    pass

            # 获取 cookies
            final_cookies = await context.cookies()
            cookies_dict = {cookie["name"]: cookie["value"] for cookie in final_cookies}

            print(f"🍪 [{self.account_name}] 获取到 {len(cookies_dict)} 个 cookies")
            for name in KEY_COOKIE_NAMES:
                if name in cookies_dict:
                    print(f"   关键cookie {name}: {cookies_dict[name][:50]}...")

            # 提取用户信息
            user_id, user_name = await self._extract_user_info(cookies_dict)

            print(f"✅ [{self.account_name}] Linux.do 认证成功")
            return {
                "success": True,
                "cookies": cookies_dict,
                "user_id": user_id,
                "username": user_name
            }

        except Exception as e:
            return {"success": False, "error": f"Linux.do 认证失败: {str(e)}"}


# ==================== 签到管理类 ====================
class AgentRouterCheckIn:
    """AgentRouter 签到管理"""

    def __init__(self, account_config: Dict, account_index: int):
        self.account_config = account_config
        self.account_index = account_index
        self.account_name = account_config.get("name", f"账号{account_index + 1}")

    async def execute(self) -> Dict:
        """执行签到"""
        print(f"\n{'='*60}")
        print(f"📝 [{self.account_name}] 开始签到")
        print(f"{'='*60}")

        # 尝试所有认证方式
        auth_methods = self._parse_auth_methods()

        if not auth_methods:
            return {
                "success": False,
                "account": self.account_name,
                "error": "未配置任何认证方式"
            }

        async with async_playwright() as playwright:
            for auth_type, auth_config in auth_methods:
                print(f"\n🔐 [{self.account_name}] 尝试 {auth_type} 认证...")

                try:
                    result = await self._checkin_with_auth(playwright, auth_type, auth_config)
                    if result["success"]:
                        return result
                    else:
                        print(f"❌ [{self.account_name}] {auth_type} 认证失败: {result.get('error')}")
                except Exception as e:
                    print(f"❌ [{self.account_name}] {auth_type} 认证异常: {str(e)}")

        # 所有认证方式都失败
        return {
            "success": False,
            "account": self.account_name,
            "error": "所有认证方式都失败"
        }

    def _parse_auth_methods(self) -> List[Tuple[str, Dict]]:
        """解析认证方式"""
        methods = []

        # Cookies 认证
        if "cookies" in self.account_config and self.account_config["cookies"]:
            methods.append(("cookies", {"cookies": self.account_config["cookies"]}))

        # 邮箱认证
        if "email" in self.account_config:
            email_config = self.account_config["email"]
            methods.append(("email", {
                "email": email_config.get("username") or email_config.get("email"),
                "password": email_config.get("password")
            }))

        # GitHub 认证
        if "github" in self.account_config:
            github_config = self.account_config["github"]
            methods.append(("github", {
                "username": github_config.get("username"),
                "password": github_config.get("password")
            }))

        # Linux.do 认证
        if "linux.do" in self.account_config:
            linuxdo_config = self.account_config["linux.do"]
            methods.append(("linux.do", {
                "username": linuxdo_config.get("username"),
                "password": linuxdo_config.get("password")
            }))

        return methods

    async def _checkin_with_auth(self, playwright, auth_type: str, auth_config: Dict) -> Dict:
        """使用指定认证方式签到"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 启动浏览器
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=temp_dir,
                headless=BROWSER_HEADLESS,
                user_agent=DEFAULT_USER_AGENT,
                viewport={"width": 1920, "height": 1080},
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )

            page = await context.new_page()

            # 用于捕获签到信息
            checkin_info = {"found": False, "message": "", "reward": ""}

            # 监听所有网络响应，捕获签到相关信息
            async def handle_response(response):
                try:
                    url = response.url
                    method = response.request.method

                    # 关注所有API请求
                    if "/api/" in url:
                        # 打印请求方法和URL
                        print(f"📡 [{method}] {url} -> {response.status}")

                        # 尝试解析JSON响应
                        if response.status == 200:
                            try:
                                json_data = await response.json()
                                # 打印响应数据（前500字符）
                                print(f"   响应: {json.dumps(json_data, ensure_ascii=False)[:500]}")

                                # 检查是否包含签到相关信息
                                if isinstance(json_data, dict):
                                    # 查找签到消息
                                    message = json_data.get("message") or json_data.get("msg") or ""

                                    # 扩大关键词匹配范围
                                    if any(keyword in message.lower() for keyword in ["签到", "sign", "check", "今日", "已", "成功"]):
                                        checkin_info["found"] = True
                                        checkin_info["message"] = message
                                        print(f"🎯 [{self.account_name}] 捕获签到响应: {url}")
                                        print(f"   消息: {message}")

                                        # 尝试提取奖励金额
                                        if "data" in json_data:
                                            data = json_data["data"]
                                            if isinstance(data, dict):
                                                # 查找可能的奖励字段
                                                for key in ["reward", "amount", "quota", "balance", "credit", "income"]:
                                                    if key in data:
                                                        checkin_info["reward"] = str(data[key])
                                                        print(f"   奖励: {data[key]}")
                                                        break

                                    # 即使消息不匹配，也检查是否有签到相关的字段
                                    if "sign" in url.lower() or "checkin" in url.lower():
                                        checkin_info["found"] = True
                                        checkin_info["message"] = message or "签到成功"
                                        print(f"🎯 [{self.account_name}] 检测到签到API调用: {url}")

                                        if "data" in json_data and isinstance(json_data["data"], dict):
                                            data = json_data["data"]
                                            for key in ["reward", "amount", "quota", "balance", "credit", "income"]:
                                                if key in data:
                                                    checkin_info["reward"] = str(data[key])
                                                    print(f"   奖励: {data[key]}")
                                                    break
                            except Exception as e:
                                if DEBUG_MODE:
                                    print(f"  [DEBUG] JSON解析失败: {e}")
                except Exception as e:
                    if DEBUG_MODE:
                        print(f"  [DEBUG] 响应处理异常: {e}")

            page.on("response", handle_response)

            try:
                # 步骤1: 获取 WAF cookies
                await self._get_waf_cookies(page, context)

                # 步骤2: 执行认证
                authenticator = self._get_authenticator(auth_type, auth_config)
                auth_result = await authenticator.authenticate(page, context)

                if not auth_result["success"]:
                    return {
                        "success": False,
                        "account": self.account_name,
                        "error": auth_result.get("error")
                    }

                print(f"✅ [{self.account_name}] 认证成功")

                # 获取认证后的 cookies
                cookies = auth_result.get("cookies", {})

                # 等待一下，确保所有网络请求都被捕获
                await page.wait_for_timeout(2000)

                # 步骤3: 检查网络监听中是否捕获到签到信息
                print(f"🎯 [{self.account_name}] 检查签到状态...")
                checkin_msg = "登录签到完成（签到在登录时自动触发）"

                if checkin_info["found"]:
                    print(f"✅ [{self.account_name}] 检测到签到响应")
                    checkin_msg = checkin_info["message"]
                    if checkin_info["reward"]:
                        checkin_msg += f" | 奖励: {checkin_info['reward']}"
                else:
                    print(f"💡 [{self.account_name}] {checkin_msg}")

                # AgentRouter的签到机制说明：
                # - 登录时自动完成签到，无需调用额外API
                # - 用户信息API需要access token，无法通过cookie访问
                # - 因此登录成功即表示签到成功

                user_info = {
                    "success": True,
                    "message": "登录成功，签到自动完成"
                }

                return {
                    "success": True,
                    "account": self.account_name,
                    "auth_method": auth_type,
                    "user_info": user_info,
                    "username": auth_result.get("username"),
                    "message": checkin_msg,
                    "checkin_reward": checkin_info.get("reward", "")
                }

            finally:
                await page.close()
                await context.close()

    def _get_authenticator(self, auth_type: str, auth_config: Dict) -> BaseAuthenticator:
        """获取认证器"""
        if auth_type == "cookies":
            return CookiesAuthenticator(self.account_name, auth_config)
        elif auth_type == "email":
            return EmailAuthenticator(self.account_name, auth_config)
        elif auth_type == "github":
            return GitHubAuthenticator(self.account_name, auth_config)
        elif auth_type == "linux.do":
            return LinuxDoAuthenticator(self.account_name, auth_config)
        else:
            raise ValueError(f"未知认证方式: {auth_type}")

    async def _get_waf_cookies(self, page: Page, context: BrowserContext):
        """获取 WAF cookies"""
        try:
            print(f"ℹ️ [{self.account_name}] 获取 WAF cookies...")
            await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT)
            await page.wait_for_timeout(2000)

            cookies = await context.cookies()
            waf_cookies = [c for c in cookies if c["name"] in WAF_COOKIE_NAMES]

            if waf_cookies:
                print(f"✅ [{self.account_name}] 获取到 {len(waf_cookies)} 个 WAF cookies")
            else:
                print(f"⚠️ [{self.account_name}] 未获取到 WAF cookies")
        except Exception as e:
            print(f"⚠️ [{self.account_name}] 获取 WAF cookies 失败: {e}")

    async def _do_checkin(self, cookies: Dict[str, str]) -> Tuple[bool, str]:
        """调用签到API"""
        try:
            print(f"📡 [{self.account_name}] 调用签到接口...")
            headers = {
                "User-Agent": DEFAULT_USER_AGENT,
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(cookies=cookies, timeout=10.0, verify=True) as client:
                response = await client.post(CHECKIN_URL, headers=headers)

                if DEBUG_MODE:
                    print(f"  [DEBUG] 签到响应状态码: {response.status_code}")
                    print(f"  [DEBUG] 签到响应内容: {response.text}")

                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get("success") or data.get("ret") == 1:
                            message = data.get("message", data.get("msg", "签到成功"))
                            print(f"✅ [{self.account_name}] {message}")
                            return True, message
                        else:
                            error_msg = data.get("message", data.get("msg", "签到失败"))
                            print(f"⚠️ [{self.account_name}] {error_msg}")
                            return False, error_msg
                    except:
                        # JSON解析失败，可能是HTML响应
                        print(f"⚠️ [{self.account_name}] 签到响应格式异常")
                        return False, "响应格式异常"
                elif response.status_code == 404:
                    # 签到接口不存在，可能已废弃
                    print(f"ℹ️ [{self.account_name}] 签到接口返回404，可能已废弃")
                    return True, "签到接口不存在（可能已废弃）"
                else:
                    print(f"❌ [{self.account_name}] 签到请求失败: HTTP {response.status_code}")
                    return False, f"HTTP {response.status_code}"

        except Exception as e:
            print(f"❌ [{self.account_name}] 签到异常: {e}")
            return False, str(e)

    async def _get_user_info(self, cookies: Dict[str, str]) -> Optional[Dict]:
        """获取用户信息"""
        try:
            # 打印将要使用的cookies
            print(f"🍪 [{self.account_name}] 准备调用用户信息API，使用 {len(cookies)} 个 cookies")
            for name in KEY_COOKIE_NAMES:
                if name in cookies:
                    print(f"   {name}: {cookies[name][:30]}...")

            headers = {"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/json"}
            async with httpx.AsyncClient(cookies=cookies, timeout=10.0, verify=True) as client:
                response = await client.get(USER_INFO_URL, headers=headers)

                print(f"📡 [{self.account_name}] 用户信息API响应:")
                print(f"   状态码: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    # 打印完整的用户数据以便调试
                    print(f"   完整数据: {json.dumps(data, ensure_ascii=False, indent=2)}")

                    if data.get("success") and data.get("data"):
                        user_data = data["data"]
                        quota = user_data.get("quota", 0) / QUOTA_TO_DOLLAR_RATE
                        used = user_data.get("used_quota", 0) / QUOTA_TO_DOLLAR_RATE

                        # 检查是否有签到相关字段
                        checkin_status = user_data.get("checkin_status") or user_data.get("signin_status") or user_data.get("daily_checkin")
                        if checkin_status:
                            print(f"   签到状态: {checkin_status}")

                        return {
                            "success": True,
                            "quota": round(quota, 2),
                            "used": round(used, 2),
                            "display": f"余额: ${quota:.2f}, 已用: ${used:.2f}",
                            "checkin_status": checkin_status
                        }
        except Exception as e:
            print(f"⚠️ [{self.account_name}] 获取用户信息失败: {e}")
        return None


# ==================== 主函数 ====================
def load_accounts() -> Optional[List[Dict]]:
    """加载账号配置"""
    accounts_str = os.getenv("AGENTROUTER_ACCOUNTS")
    if not accounts_str:
        print("❌ 未设置 AGENTROUTER_ACCOUNTS 环境变量")
        return None

    try:
        accounts = json.loads(accounts_str)
        if not isinstance(accounts, list):
            print("❌ AGENTROUTER_ACCOUNTS 格式错误，应为 JSON 数组")
            return None
        return accounts
    except Exception as e:
        print(f"❌ 解析 AGENTROUTER_ACCOUNTS 失败: {e}")
        return None


async def main_async():
    """异步主函数"""
    print("="*80)
    print("🚀 AgentRouter 自动签到脚本 (重构版)")
    print(f"🕒 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 基础URL: {BASE_URL}")
    print(f"🖥️  浏览器模式: {'无头' if BROWSER_HEADLESS else '有头'}")
    print("="*80)

    # 加载账号
    accounts = load_accounts()
    if not accounts:
        print("❌ 无法加载账号配置")
        return 1

    print(f"\n✅ 找到 {len(accounts)} 个账号配置\n")

    # 执行签到
    results = []
    for i, account in enumerate(accounts):
        try:
            checkin = AgentRouterCheckIn(account, i)
            result = await checkin.execute()
            results.append(result)
        except Exception as e:
            print(f"❌ 账号 {i+1} 处理异常: {e}")
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

    print(f"\n{'='*80}")
    print(f"📊 签到结果统计")
    print(f"{'='*80}")
    print(f"✅ 成功: {success_count}/{total_count}")
    print(f"❌ 失败: {total_count - success_count}/{total_count}")

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
    notification_lines.append(f"⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    notification_content = "\n".join(notification_lines)

    print(f"\n{notification_content}\n")

    # 发送通知 (只在有失败时发送)
    if success_count < total_count:
        safe_send_notify("[AgentRouter]签到结果", notification_content)

    print(f"{'='*80}\n")

    return 0 if success_count > 0 else 1


def main():
    """同步主函数入口"""
    try:
        return asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n⚠️ 程序被用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
