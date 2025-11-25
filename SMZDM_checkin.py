"""
cron: 39 17 * * *
new Env('什么值得买签到')
"""
import sys
import io

# 设置标准输出编码为UTF-8（解决Windows环境emoji显示问题）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests, json, time, hashlib, os, random, re
from datetime import datetime, timedelta

# ---------------- 日志类 ----------------
class Logger:
    def __init__(self):
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"

    def log(self, level, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] [{level}] {message}"
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

# ---------------- 通知模块动态加载 ----------------
hadsend = False
send = None
try:
    from notify import send
    hadsend = True
    logger.info("已加载notify.py通知模块")
except ImportError:
    logger.info("未加载通知模块，跳过通知功能")

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

def get_user_info(cookie):
    """获取用户基本信息"""
    logger.info("开始获取用户信息...")
    try:
        infourl = 'https://zhiyou.smzdm.com/user/'
        headers = {
            'Host': 'zhiyou.smzdm.com',
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'Cookie': cookie,
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148/smzdm 10.4.6 rv:130.1 (iPhone 13; iOS 15.6; zh_CN)/iphone_smzdmapp/10.4.6/wkwebview/jsbv_1.0.0',
            'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
            'Referer': 'https://m.smzdm.com/',
            'Accept-Encoding': 'gzip, deflate, br'
        }

        response_info = requests.get(url=infourl, headers=headers, timeout=15)

        logger.debug(f"API 请求：GET {infourl} {response_info.status_code}")
        logger.debug(f"响应：{response_info.text[:300]}")

        # 解析用户信息
        name_match = re.search(r'<a href="https://zhiyou.smzdm.com/user"> (.*?) </a>', response_info.text)
        level_match = re.search(r'<img src=".*?/level/(\d+).png.*?"', response_info.text)
        gold_match = re.search(r'<div class="assets-part assets-gold">.*?<span class="assets-part-element assets-num">(.*?)</span>', response_info.text, re.S)
        silver_match = re.search(r'<div class="assets-part assets-prestige">.*?<span class="assets-part-element assets-num">(.*?)</span>', response_info.text, re.S)

        name = name_match.group(1).strip() if name_match else "未知用户"
        level = level_match.group(1) if level_match else "0"
        gold = gold_match.group(1).strip() if gold_match else "0"
        silver = silver_match.group(1).strip() if silver_match else "0"

        logger.info(f"获取用户信息成功: 用户={name}, VIP{level}, 金币={gold}, 碎银={silver}")

        return name, level, gold, silver
    except Exception as e:
        logger.error(f"获取失败，原因：{e}")
        return "未知用户", "0", "0", "0"

def get_monthly_exp(cookie):
    """获取本月经验"""
    logger.info("开始获取本月经验...")
    try:
        current_month = datetime.now().strftime('%Y-%m')
        total_exp = 0

        for page in range(1, 4):  # 查询前3页
            url = f'https://zhiyou.m.smzdm.com/user/exp/ajax_log?page={page}'
            headers = {
                'Host': 'zhiyou.m.smzdm.com',
                'Accept': 'application/json, text/plain, */*',
                'Connection': 'keep-alive',
                'Cookie': cookie,
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148/smzdm 10.4.40 rv:137.6 (iPhone 13; iOS 15.6; zh_CN)/iphone_smzdmapp/10.4.40/wkwebview/jsbv_1.0.0',
                'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
                'Referer': 'https://zhiyou.m.smzdm.com/user/exp/',
                'Accept-Encoding': 'gzip, deflate, br'
            }

            resp = requests.get(url=url, headers=headers, timeout=10)

            logger.debug(f"API 请求：GET {url} {resp.status_code}")
            logger.debug(f"响应：{resp.text[:300]}")

            if resp.status_code != 200:
                break

            result = resp.json()
            rows = result.get('data', {}).get('rows', [])

            if not rows:
                break

            for row in rows:
                exp_date = row.get('creation_date', '')[:7]
                if exp_date == current_month:
                    total_exp += int(row.get('add_exp', 0))
                elif exp_date < current_month:
                    # 如果日期小于当前月份，说明已经查完了
                    logger.info(f"查询完成，原因：本月经验={total_exp}")
                    return total_exp

            # 添加请求间隔
            time.sleep(random.uniform(0.5, 1.5))

        logger.info(f"查询完成，原因：本月经验={total_exp}")
        return total_exp
    except Exception as e:
        logger.error(f"查询失败，原因：{e}")
        return 0

def smzdm_signin(cookie, index):
    """什么值得买签到 - 单个账号"""
    logger.info(f"==== 开始第{index}个帐号签到 ====")

    try:
        # 0. 获取用户信息
        name, level, gold, silver = get_user_info(cookie)

        # 1. 获取Token
        logger.info("开始获取Token...")
        ts = int(round(time.time() * 1000))
        url = 'https://user-api.smzdm.com/robot/token'
        headers = {
            'Host': 'user-api.smzdm.com',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': cookie,
            'User-Agent': 'smzdm_android_V10.4.1 rv:841 (22021211RC;Android12;zh)smzdmapp',
        }
        data = {
            "f": "android",
            "v": "10.4.1",
            "weixin": 1,
            "time": ts,
            "sign": hashlib.md5(bytes(f'f=android&time={ts}&v=10.4.1&weixin=1&key=apr1$AwP!wRRT$gJ/q.X24poeBInlUJC', encoding='utf-8')).hexdigest().upper()
        }

        html = requests.post(url=url, headers=headers, data=data, timeout=15)

        logger.debug(f"API 请求：POST {url} {html.status_code}")
        logger.debug(f"响应：{html.text[:300]}")

        # 检查HTTP状态码
        if html.status_code != 200:
            error_msg = f"账号{index}: HTTP请求失败，状态码: {html.status_code}"
            logger.error(error_msg)
            return error_msg, False

        # 尝试解析JSON
        try:
            result = html.json()
        except json.JSONDecodeError as e:
            error_msg = f"账号{index}: 响应不是有效的JSON格式 - {str(e)}"
            logger.error(error_msg)
            return error_msg, False

        # 检查API返回的错误码
        error_code = result.get('error_code')
        error_msg_api = result.get('error_msg', '未知错误')

        if str(error_code) != "0":
            error_msg = f"账号{index}: Token获取失败 - 错误码: {error_code}, 错误信息: {error_msg_api}"
            logger.error(error_msg)
            return error_msg, False

        # 检查是否有data字段和token
        if 'data' not in result or 'token' not in result['data']:
            error_msg = f"账号{index}: 响应中缺少token数据 - {result}"
            logger.error(error_msg)
            return error_msg, False

        token = result['data']['token']
        logger.info("Token获取成功")

        # 2. 执行签到
        logger.info("开始执行签到...")
        Timestamp = int(round(time.time() * 1000))
        sign_data = {
            "f": "android",
            "v": "10.4.1",
            "sk": "ierkM0OZZbsuBKLoAgQ6OJneLMXBQXmzX+LXkNTuKch8Ui2jGlahuFyWIzBiDq/L",
            "weixin": 1,
            "time": Timestamp,
            "token": token,
            "sign": hashlib.md5(bytes(f'f=android&sk=ierkM0OZZbsuBKLoAgQ6OJneLMXBQXmzX+LXkNTuKch8Ui2jGlahuFyWIzBiDq/L&time={Timestamp}&token={token}&v=10.4.1&weixin=1&key=apr1$AwP!wRRT$gJ/q.X24poeBInlUJC', encoding='utf-8')).hexdigest().upper()
        }

        # 签到请求
        url_signin = 'https://user-api.smzdm.com/checkin'
        html_signin = requests.post(url=url_signin, headers=headers, data=sign_data, timeout=15)

        logger.debug(f"API 请求：POST {url_signin} {html_signin.status_code}")
        logger.debug(f"响应：{html_signin.text[:300]}")

        if html_signin.status_code != 200:
            error_msg = f"账号{index}: 签到HTTP请求失败，状态码: {html_signin.status_code}"
            logger.error(error_msg)
            return error_msg, False

        try:
            signin_result = html_signin.json()
        except json.JSONDecodeError as e:
            error_msg = f"账号{index}: 签到响应不是有效的JSON格式 - {str(e)}"
            logger.error(error_msg)
            return error_msg, False

        signin_msg = signin_result.get('error_msg', '签到状态未知')
        signin_code = signin_result.get('error_code', -1)
        logger.info(f"签到完成，原因：{signin_msg}")

        # 3. 获取签到奖励
        logger.info("开始查询签到奖励...")
        url_reward = 'https://user-api.smzdm.com/checkin/all_reward'
        html_reward = requests.post(url=url_reward, headers=headers, data=sign_data, timeout=15)

        logger.debug(f"API 请求：POST {url_reward} {html_reward.status_code}")
        logger.debug(f"响应：{html_reward.text[:300]}")

        reward_info = ""
        if html_reward.status_code == 200:
            try:
                reward_result = html_reward.json()

                if str(reward_result.get('error_code')) == "0" and reward_result.get('data'):
                    normal_reward = reward_result["data"].get("normal_reward", {})
                    if normal_reward:
                        reward_content = normal_reward.get("reward_add", {}).get("content", "无奖励")
                        sub_title = normal_reward.get("sub_title", "无连续签到信息")
                        reward_info = f"\n🎁 签到奖励: {reward_content}\n📅 连续签到: {sub_title}"
                        logger.info(f"查询奖励成功: 奖励={reward_content}, 连续={sub_title}")
            except Exception as e:
                logger.warning(f"奖励信息解析失败: {e}")
        else:
            logger.warning(f"奖励查询失败，状态码: {html_reward.status_code}")

        # 4. 获取本月经验
        monthly_exp = get_monthly_exp(cookie)

        # 5. 组合结果消息（统一模板格式）
        final_msg = f"""🌐 域名：www.smzdm.com

👤 账号{index}：
📱 用户：{name}
⭐ 等级：VIP{level}
💰 金币：{gold}
🪙 碎银：{silver}
📊 本月经验：{monthly_exp}
📝 签到：{signin_msg}
📊 状态码：{signin_code}{reward_info}
⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        # 判断是否成功
        is_success = (str(signin_code) == "0" or
                     "成功" in signin_msg or
                     "已经" in signin_msg or
                     "重复" in signin_msg or
                     "已签" in signin_msg)

        logger.info(f"{'签到成功' if is_success else '签到失败'}")
        return final_msg, is_success

    except requests.exceptions.Timeout:
        error_msg = f"账号{index}: 请求超时，网络连接可能有问题"
        logger.error(error_msg)
        return error_msg, False
    except requests.exceptions.ConnectionError:
        error_msg = f"账号{index}: 网络连接错误，无法连接到服务器"
        logger.error(error_msg)
        return error_msg, False
    except Exception as e:
        error_msg = f"账号{index}: 签到异常 - {str(e)}"
        logger.error(error_msg)
        return error_msg, False

def main():
    """主程序入口"""
    logger.info(f"==== 什么值得买签到开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====")

    # 获取环境变量
    SMZDM_COOKIE_env = os.getenv("SMZDM_COOKIE")

    if not SMZDM_COOKIE_env:
        error_msg = "未找到SMZDM_COOKIE环境变量，请设置什么值得买Cookie"
        logger.error(error_msg)
        safe_send_notify("[什么值得买]签到失败", error_msg)
        return

    # 解析多账号Cookie
    SMZDM_COOKIEs = SMZDM_COOKIE_env.split('&')
    logger.info(f"共发现 {len(SMZDM_COOKIEs)} 个账号")

    success_count = 0
    total_count = len(SMZDM_COOKIEs)

    for i, cookie in enumerate(SMZDM_COOKIEs):
        try:
            # 账号间随机等待
            if i > 0:
                delay = random.uniform(5, 15)
                logger.info(f"随机等待 {delay:.1f} 秒后处理下一个账号...")
                time.sleep(delay)

            # 执行签到
            result_msg, is_success = smzdm_signin(cookie.strip(), i + 1)

            if is_success:
                success_count += 1

            # 发送单个账号通知（统一格式）
            title = f"[什么值得买]签到{'成功' if is_success else '失败'}"
            safe_send_notify(title, result_msg)

        except Exception as e:
            error_msg = f"账号{i + 1}: 处理异常 - {str(e)}"
            logger.error(error_msg)
            safe_send_notify("[什么值得买]签到失败", error_msg)

    # 发送汇总通知（统一格式）
    if total_count > 1:
        summary_msg = f"""🌐 域名：www.smzdm.com

📊 签到汇总：
✅ 成功：{success_count}个
❌ 失败：{total_count - success_count}个
📈 成功率：{success_count/total_count*100:.1f}%
⏰ 完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        safe_send_notify("[什么值得买]签到汇总", summary_msg)

    logger.info(f"==== 什么值得买签到完成 - 成功{success_count}/{total_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====")

if __name__ == "__main__":
    main()
