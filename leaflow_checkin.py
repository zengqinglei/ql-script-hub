# -*- coding: utf-8 -*-
"""
cron "34 18 * * *" script-path=leaflow_checkin.py,tag=匹配cron用
new Env('leaflow签到')
"""
import os
import re
import sys
import time
import json
import random
from datetime import datetime, timedelta

try:
    from zoneinfo import ZoneInfo
    SH_TZ = ZoneInfo("Asia/Shanghai")
except Exception:
    SH_TZ = None


try:
    from curl_cffi import requests
    USE_CURL_CFFI = True
except ImportError:
    import requests
    USE_CURL_CFFI = False

# ---------------- 可选通知模块 ----------------
hadsend = False
try:
    from notify import send
    hadsend = True
    print("✅ 通知模块加载成功")
except Exception as e:
    print(f"⚠️ 通知模块加载失败: {e}")
    def send(title, content):
        pass

# ---------------- 配置项 ----------------
LEAFLOW_DOMAIN = os.getenv("LEAFLOW_DOMAIN", "https://leaflow.net").rstrip("/")
BASE = os.getenv("LEAFLOW_BASE", "https://checkin.leaflow.net").rstrip("/")
TIMEOUT = int(os.getenv("TIMEOUT", "60"))
RETRY_TIMES = int(os.getenv("RETRY_TIMES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))
RANDOM_SIGNIN = os.getenv("RANDOM_SIGNIN", "true").lower() == "true"
MAX_RANDOM_DELAY = int(os.getenv("MAX_RANDOM_DELAY", "3600"))
NOTIFY_ON_ALREADY = os.getenv("NOTIFY_ON_ALREADY", "true").lower() == "true"  # 已签到是否通知
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"  # 调试模式

HTTP_PROXY = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
HTTPS_PROXY = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
PROXIES = None
if HTTP_PROXY or HTTPS_PROXY:
    PROXIES = {"http": HTTP_PROXY or HTTPS_PROXY, "https": HTTPS_PROXY or HTTP_PROXY}

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

def now_sh():
    return datetime.now(tz=SH_TZ) if SH_TZ else datetime.now()

def parse_cookie_array(cookie_str: str) -> list:
    """
    解析 JSON 数组格式的 cookie 配置
    格式: [{"leaflow_session":"xxx","remember_web_xxx":"yyy","XSRF-TOKEN":"zzz"}]
    """
    try:
        cookies_array = json.loads(cookie_str.strip())
        if not isinstance(cookies_array, list):
            raise ValueError("Cookie 必须是 JSON 数组格式")

        # 验证每个元素都是有效的 cookie 字典
        for i, item in enumerate(cookies_array):
            if not isinstance(item, dict):
                raise ValueError(f"Cookie 数组第 {i+1} 个元素必须是 JSON 对象格式")
            # 检查必需的 cookie 键
            required_keys = ['leaflow_session', 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d', 'XSRF-TOKEN']
            missing_keys = [key for key in required_keys if key not in item]
            if missing_keys:
                raise ValueError(f"Cookie 数组第 {i+1} 个元素缺少必需的键: {', '.join(missing_keys)}")

        return cookies_array
    except json.JSONDecodeError as e:
        raise ValueError(f"Cookie JSON 数组解析失败: {e}")


def build_session(account_config):
    """
    构建会话（JSON数组格式的cookies字典）
    """
    s = requests.Session()

    # 设置完整的浏览器 headers
    s.headers.update({
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
    })

    # account_config 是包含 cookies 的字典
    if DEBUG_MODE:
        print(f"  [DEBUG] 解析到的 cookies: {list(account_config.keys())}")

    for name, value in account_config.items():
        # 设置所有cookie（包括XSRF-TOKEN）
        # 注意：XSRF-TOKEN可能过期导致首次请求423，但服务器会返回新token，重试即可成功
        s.cookies.set(name, value, domain='.leaflow.net')

    if PROXIES:
        s.proxies.update(PROXIES)

    return s

def extract_csrf(html: str) -> dict:
    data = {}
    for m in re.finditer(r'<input[^>]+type=["\']hidden["\'][^>]*>', html, re.I):
        tag = m.group(0)
        name_match = re.search(r'name=["\']([^"\']+)["\']', tag)
        value_match = re.search(r'value=["\']([^"\']*)["\']', tag)
        if name_match:
            data[name_match.group(1)] = value_match.group(1) if value_match else ""
    return data

def extract_reward(html: str) -> float:
    """
    🔧 修复版本：优先匹配今日签到奖励，避免误取历史记录
    """
    if not html:
        return 0

    # 清理脚本和样式标签
    text_cleaned = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.I)
    text_cleaned = re.sub(r'<style[^>]*>.*?</style>', '', text_cleaned, flags=re.DOTALL | re.I)

    # 🆕 移除签到历史区域（避免误匹配历史金额）
    text_cleaned = re.sub(
        r'<div[^>]*class=["\'][^"\']*history[^"\']*["\'][^>]*>.*?</div>',
        '',
        text_cleaned,
        flags=re.DOTALL | re.I
    )
    text_cleaned = re.sub(
        r'签到历史.*?(?=<div|$)',
        '',
        text_cleaned,
        flags=re.DOTALL | re.I
    )

    if DEBUG_MODE:
        print(f"[DEBUG] 清理后的HTML片段: {text_cleaned[:300]}...")

    # 🆕 优先级1：明确匹配"今日/今天/本次/签到成功"相关的奖励
    priority_patterns = [
        r'今日.*?获得.*?([\d.]+)\s*元',
        r'今天.*?获得.*?([\d.]+)\s*元',
        r'本次.*?获得.*?([\d.]+)\s*元',
        r'签到成功.*?获得.*?([\d.]+)\s*元',
        r'今日签到.*?([\d.]+)\s*元',
        r'恭喜.*?获得.*?([\d.]+)\s*元',
        r'成功.*?奖励.*?([\d.]+)\s*元',
    ]

    for pattern in priority_patterns:
        match = re.search(pattern, text_cleaned, re.I)
        if match:
            try:
                amount = float(match.group(1))
                if 0.01 <= amount <= 10:
                    if DEBUG_MODE:
                        print(f"[DEBUG] 优先级匹配成功: {pattern} -> {amount} 元")
                    return amount
            except (ValueError, IndexError):
                continue

    # 🆕 优先级2：通用模式（从前往后找第一个，而非最大值）
    general_patterns = [
        r'\+\s*([\d.]+)\s*元',
        r'([\d.]+)\s*元',
        r'获得.*?([\d.]+)\s*元',
        r'奖励.*?([\d.]+)\s*元',
        r'领取.*?([\d.]+)\s*元',
    ]
    for pattern in general_patterns:
        match = re.search(pattern, text_cleaned, re.I)  # 🔄 改为 search（找第一个）
        if match:
            try:
                amount = float(match.group(1))
                if 0.01 <= amount <= 10:
                    if DEBUG_MODE:
                        print(f"[DEBUG] 通用模式匹配: {pattern} -> {amount} 元")
                    return amount
            except (ValueError, IndexError):
                continue

    if DEBUG_MODE:
        print("[DEBUG] 未匹配到任何金额")
    return 0

def get_user_balance_info(session) -> tuple[dict, str]:
    """
    获取用户余额和账户信息 - 通过API接口
    """
    try:
        kwargs = {"timeout": TIMEOUT, "allow_redirects": True}
        if USE_CURL_CFFI:
            kwargs["impersonate"] = "chrome120"

        # 设置最小必要的API请求headers
        api_headers = {
            'X-Inertia-Version': '98497d2ccb64ae33c0053ceb4d917dfc',
            'X-Inertia': 'true',
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'text/html, application/xhtml+xml',
            'Accept-Encoding': 'gzip, deflate'  # 只接受 gzip 和 deflate，不接受 br
        }

        # 从session的cookies中获取XSRF-TOKEN（使用字典访问方式避免多个同名cookie报错）
        xsrf_token = session.cookies.get_dict().get('XSRF-TOKEN')
        if xsrf_token:
            api_headers['X-XSRF-TOKEN'] = xsrf_token

        # 设置Referer
        api_headers['Referer'] = f'{LEAFLOW_DOMAIN}/dashboard'

        # 更新session的headers
        session.headers.update(api_headers)

        # 访问余额API接口
        balance_url = f"{LEAFLOW_DOMAIN}/balance"
        r = session.get(balance_url, **kwargs)

        if r.status_code != 200:
            return {}, f"余额API访问失败: {r.status_code}"

        # 解析JSON响应
        try:
            data = r.json()
        except json.JSONDecodeError as e:
            return {}, f"JSON解析失败: {str(e)}"

        # 提取用户信息
        auth_data = data.get("props", {}).get("auth", {})
        user_data = auth_data.get("user", {})

        if not user_data:
            return {}, "JSON中未找到用户信息"

        user_info = {
            "username": user_data.get("name", "未知用户"),
            "email": user_data.get("email", ""),
            "current_balance": float(user_data.get("current_balance", 0)),
            "total_consumed": float(user_data.get("total_consumed", 0))
        }

        return user_info, "获取账户信息成功"

    except requests.exceptions.Timeout:
        return {}, f"获取账户信息超时（{TIMEOUT}秒）"
    except requests.exceptions.ConnectionError as e:
        return {}, f"获取账户信息连接失败: {str(e)[:80]}"
    except Exception as e:
        return {}, f"获取账户信息异常: {str(e)[:100]}"

def parse_result(html: str) -> tuple[str, str, float]:
    if not html:
        return "unknown", "页面内容为空", 0

    # 🔧 优先检测：如果存在"立即签到"按钮，说明未签到（此时不提取金额）
    if re.search(r'立即签到|<button[^>]+name=["\']checkin["\']', html, re.I):
        if DEBUG_MODE:
            print("[DEBUG] 检测到'立即签到'按钮，判断为未签到状态")
        return "unknown", "检测到签到按钮，需要执行签到", 0

    # 🔧 修复：更精确的已签到模式
    already_patterns = [
        r'今日已签到',
        r'明天再来',
        r'已签到',
        r'already\s+checked',
    ]
    for pattern in already_patterns:
        if re.search(pattern, html, re.I):
            # ✅ 只有确认已签到后才提取金额
            amount = extract_reward(html)
            if amount > 0:
                return "already", f"今日已签到，获得 {amount} 元", amount
            return "already", "今日已签到", 0

    success_patterns = [
        r'签到成功',
        r'获得奖励',
        r'领取成功',
        r'恭喜',
        r'check-?in\s+success',
    ]
    for pattern in success_patterns:
        if re.search(pattern, html, re.I):
            # ✅ 只有确认签到成功后才提取金额
            amount = extract_reward(html)
            if amount > 0:
                return "success", f"签到成功，获得 {amount} 元", amount
            return "success", "签到成功", 0

    invalid_patterns = [
        r'请登录',
        r'please\s+log\s*in',
        r'未登录',
        r'session\s+expired',
    ]
    for pattern in invalid_patterns:
        if re.search(pattern, html, re.I):
            return "invalid", "登录失效，请更新 Cookie", 0

    if "error" in html.lower() or "错误" in html:
        return "fail", "页面返回错误", 0
    return "unknown", "未识别到明确状态", 0
def sign_once_impl(session) -> tuple[str, str, float]:
    """
    使用已构建的 session 执行签到
    优化：先访问签到主页预热并检测是否已签到，未签到才执行POST请求
    """
    try:
        kwargs = {"timeout": TIMEOUT, "allow_redirects": True}
        if USE_CURL_CFFI:
            kwargs["impersonate"] = "chrome120"

        # 步骤1：访问签到主页（预热session，刷新XSRF-TOKEN，获取CSRF token）
        r1 = session.get(f"{BASE}/", **kwargs)

        if "login" in r1.url.lower():
            return "invalid", "被重定向到登录页，Cookie 已失效", 0

        if r1.status_code == 403:
            return "error", "403 Forbidden（触发风控）", 0

        if r1.status_code != 200:
            return "error", f"首页返回 {r1.status_code}", 0

        html1 = r1.text or ""

        if any(x in html1 for x in ["请登录", "未登录"]):
            return "invalid", "页面提示未登录", 0

        # 步骤2：预检是否已签到（避免不必要的POST请求）
        status_precheck, msg_precheck, amount_precheck = parse_result(html1)
        if status_precheck == "already":
            # 已签到，直接返回，无需POST
            return status_precheck, msg_precheck, amount_precheck

        # 步骤3：未签到，准备CSRF token并执行POST签到请求
        form_data = {"checkin": ""}
        form_data.update(extract_csrf(html1))

        headers_post = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": BASE,
            "Referer": f"{BASE}/",
        }

        r2 = session.post(f"{BASE}/index.php", data=form_data, headers=headers_post, **kwargs)

        if r2.status_code == 403:
            return "error", "POST 被拒绝 403", 0

        html2 = r2.text or ""
        status, msg, amount = parse_result(html2)

        # 步骤4：如果POST后状态不明确，再次访问首页确认
        if status == "unknown" or (status == "success" and amount == 0):
            time.sleep(1)
            r3 = session.get(f"{BASE}/", **kwargs)
            status2, msg2, amount2 = parse_result(r3.text or "")
            if status2 != "unknown":
                return status2, msg2, amount2

        return status, msg, amount

    except requests.exceptions.Timeout:
        return "error", f"请求超时（{TIMEOUT}秒）", 0
    except requests.exceptions.ConnectionError as e:
        return "error", f"连接失败: {str(e)[:80]}", 0
    except Exception as e:
        return "error", f"{e.__class__.__name__}: {str(e)[:100]}", 0

def sign_with_retry(account_config, name: str) -> tuple[str, str, float, dict]:
    """
    执行签到并返回账户信息
    """
    # 构建 session（包含多个 cookie）
    try:
        session = build_session(account_config)
    except ValueError as e:
        return "error", f"Cookie 配置错误: {str(e)}", 0, {}

    # 执行签到（带重试，首次可能423，重试时会使用服务器下发的新XSRF-TOKEN）
    status = "unknown"
    msg = ""
    amount = 0
    for attempt in range(1, RETRY_TIMES + 1):
        if attempt > 1:
            print(f"  🔄 第 {attempt}/{RETRY_TIMES} 次重试...")
            time.sleep(RETRY_DELAY)

        status, msg, amount = sign_once_impl(session)

        # 如果Cookie失效，直接返回，不再重试
        if status == "invalid":
            return status, msg, amount, {}

        # 签到成功或已签到，跳出重试循环
        if status in ("success", "already"):
            break

        if attempt < RETRY_TIMES:
            print(f"  ⚠️ {msg}，{RETRY_DELAY}秒后重试...")

    # 如果签到失败多次，添加重试说明
    if status not in ("success", "already", "invalid"):
        msg = f"{msg}（重试 {RETRY_TIMES} 次后失败）"

    # 签到后获取账户信息（此时余额已包含签到奖励）
    print(f"  📊 获取账户信息...")
    user_info, info_msg = get_user_balance_info(session)
    if user_info:
        print(f"  👤 用户: {user_info['username']}")
        print(f"  💰 余额: {user_info['current_balance']:.2f}元")
        print(f"  💸 累计消费: {user_info['total_consumed']:.2f}元")
    else:
        print(f"  ⚠️ 获取账户信息失败: {info_msg}")

    return status, msg, amount, user_info

def format_time_remaining(seconds: int) -> str:
    if seconds <= 0:
        return "立即执行"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}小时{m}分{s}秒"
    if m > 0:
        return f"{m}分{s}秒"
    return f"{s}秒"
def wait_with_countdown(delay_seconds: int, tag: str):
    if delay_seconds <= 0:
        return
    print(f"{tag} 需要等待 {format_time_remaining(delay_seconds)}")
    remaining = delay_seconds
    while remaining > 0:
        if remaining <= 10 or remaining % 10 == 0:
            print(f"{tag} 倒计时: {format_time_remaining(remaining)}")
        step = 1 if remaining <= 10 else min(10, remaining)
        time.sleep(step)
        remaining -= step

def format_user_info(user_info: dict) -> str:
    """格式化用户信息为通知文本"""
    if not user_info:
        return ""

    lines = []

    # 用户信息：用户（邮箱）
    account_info = user_info.get('username', '未知用户')
    if user_info.get('email') and user_info.get('email') != '***@***.***':
        account_info += f"（{user_info['email']}）"
    lines.append(f"👤 用户：{account_info}")

    # 账户信息：余额，累计消费
    balance_info = f"余额 {user_info.get('current_balance', 0):.2f}元"
    if user_info.get('total_consumed', 0) > 0:
        balance_info += f"，累计消费 {user_info.get('total_consumed', 0):.2f}元"
    lines.append(f"💰 账户：{balance_info}")

    return "\n".join(lines)

def build_notify_message(name: str, msg: str, user_info: dict) -> str:
    """构建统一的通知消息格式"""
    notify_msg = f"""🌐 域名：{LEAFLOW_DOMAIN.replace('https://', '').replace('http://', '')}

👤 {name}："""

    user_info_text = format_user_info(user_info)
    if user_info_text:
        notify_msg += f"\n{user_info_text}"

    notify_msg += f"""
📝 签到：{msg}
⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

    return notify_msg

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

def main():
    print(f"{'='*50}")
    print(f"  Leaflow 签到脚本 v3.2（账户信息增强版）")
    print(f"  更新时间: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"  更新内容: 新增账户余额和用户信息显示")
    print(f"  Cookie 格式: JSON 数组 [{{\"leaflow_session\":\"xxx\",...}}]")
    if DEBUG_MODE:
        print(f"  🐛 调试模式: 已启用")
    print(f"{'='*50}\n")

    cookies_env = os.getenv("LEAFLOW_COOKIE", "").strip()
    if not cookies_env:
        print("❌ 未设置 LEAFLOW_COOKIE 环境变量")
        sys.exit(1)

    # 解析 JSON 数组格式
    try:
        cookie_list = parse_cookie_array(cookies_env)
        print(f"✅ 成功解析 Cookie 配置，共 {len(cookie_list)} 个账号")
    except ValueError as e:
        print(f"❌ Cookie 配置解析失败: {e}")
        print("💡 请确保 LEAFLOW_COOKIE 格式为 JSON 数组")
        sys.exit(1)

    print(f"随机签到: {'启用' if RANDOM_SIGNIN else '禁用'}")
    if RANDOM_SIGNIN:
        print(f"随机签到时间窗口: {MAX_RANDOM_DELAY // 60} 分钟")

    schedule = []
    base_time = now_sh()
    for i, account_config in enumerate(cookie_list, 1):
        delay = random.randint(0, MAX_RANDOM_DELAY) if RANDOM_SIGNIN else 0
        schedule.append({
            "idx": i,
            "account": account_config,
            "delay": delay,
            "time": base_time + timedelta(seconds=delay),
            "name": f"账号{i}"
        })

    schedule.sort(key=lambda x: x["delay"])

    if RANDOM_SIGNIN and len(schedule) > 1:
        print("\n==== 签到执行顺序 ====")
        for it in schedule:
            print(f"{it['name']}: 预计 {it['time'].strftime('%H:%M:%S')} 执行")

    print("\n==== 开始执行签到任务 ====\n")

    success_count = 0
    already_count = 0
    fail_count = 0
    total_amount = 0.0

    for it in schedule:
        name = it["name"]

        if it["delay"] > 0:
            wait_with_countdown(it["delay"], name)

        print(f"\n==== {name} 开始签到 ====")
        print(f"当前时间: {datetime.now().strftime('%H:%M:%S')}")

        status, msg, amount, user_info = sign_with_retry(it["account"], name)

        if status == "success":
            success_count += 1
            if amount > 0:
                total_amount += amount
                print(f"✅ {name} {msg}")
                print(f"💰 本次获得: {amount} 元")
            else:
                print(f"✅ {name} {msg}")

            # 使用统一的通知消息构建函数
            notify_msg = build_notify_message(name, msg, user_info)
            safe_send_notify("[leaflow]签到成功", notify_msg)

        elif status == "already":
            already_count += 1
            if amount > 0:
                total_amount += amount
                print(f"ℹ️ {name} {msg}")
            else:
                print(f"ℹ️ {name} 今日已签到")

            if NOTIFY_ON_ALREADY:
                # 使用统一的通知消息构建函数
                notify_msg = build_notify_message(name, msg, user_info)
                safe_send_notify("[leaflow]签到成功", notify_msg)

        else:
            fail_count += 1
            print(f"❌ {name} 签到失败: {msg}")

            # 使用统一的通知消息构建函数
            notify_msg = build_notify_message(name, msg, user_info)
            safe_send_notify("[leaflow]签到失败", notify_msg)

        if it["idx"] < len(schedule):
            time.sleep(random.uniform(2, 5))

    print(f"\n{'='*50}")
    print(f"  所有账号签到完成")
    print(f"  ✅ 成功: {success_count} | ℹ️ 已签: {already_count} | ❌ 失败: {fail_count}")

    if total_amount > 0:
        print(f"  💰 今日总计获得: {total_amount} 元")

    print(f"  完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    if len(schedule) > 1:
        # 统一汇总格式
        summary = f"""🌐 域名：{LEAFLOW_DOMAIN.replace('https://', '').replace('http://', '')}

📊 签到汇总：
✅ 成功：{success_count}个
ℹ️ 已签：{already_count}个
❌ 失败：{fail_count}个
📈 成功率：{(success_count + already_count)/len(schedule)*100:.1f}%"""
        if total_amount > 0:
            summary += f"\n💰 今日共获得：{total_amount} 元"
        summary += f"\n⏰ 完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        safe_send_notify("[leaflow]签到汇总", summary)


if __name__ == "__main__":
    main()