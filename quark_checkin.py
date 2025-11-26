# -*- coding: utf-8 -*-
"""
cron "13 18 * * *" script-path=xxx.py,tag=匹配cron用
new Env('夸克网盘签到')
"""
import sys
import io

# 设置标准输出编码为UTF-8（解决Windows环境emoji显示问题）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import re
import time
import random
import requests
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

def get_env():
    """获取环境变量"""
    if "QUARK_COOKIE" in os.environ:
        cookie_list = re.split('\n|&&', os.environ.get('QUARK_COOKIE'))
        # 过滤空字符串
        cookie_list = [c.strip() for c in cookie_list if c.strip()]
    else:
        logger.error('未添加QUARK_COOKIE变量')
        sys.exit(0)

    return cookie_list

class Quark:
    """夸克网盘签到类"""

    def __init__(self, cookie):
        """初始化"""
        self.cookie = cookie
        self.param = self._parse_cookie(cookie)

    def _parse_cookie(self, cookie):
        """解析cookie为字典"""
        logger.debug("开始解析Cookie...")
        user_data = {}
        for item in cookie.replace(" ", "").split(';'):
            if item and '=' in item:
                key, value = item.split('=', 1)
                user_data[key] = value
        logger.debug(f"解析完成，获取到 {len(user_data)} 个参数")
        return user_data

    def convert_bytes(self, b):
        """将字节转换为可读格式"""
        units = ("B", "KB", "MB", "GB", "TB", "PB")
        i = 0
        while b >= 1024 and i < len(units) - 1:
            b /= 1024
            i += 1
        return f"{b:.2f}{units[i]}"

    def get_growth_info(self):
        """获取签到信息"""
        logger.info("开始获取账号信息...")

        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        try:
            response = requests.get(url=url, params=querystring, timeout=10)

            logger.debug(f"API 请求：GET {url} {response.status_code}")
            logger.debug(f"响应：{response.text[:300]}")

            response_data = response.json()
            if response_data.get("data"):
                logger.info("账号信息获取成功")
                return response_data["data"]
            else:
                # 记录详细错误信息
                error_msg = response_data.get("message", "未知错误")
                error_code = response_data.get("code", "")
                logger.error(f"API返回错误: 错误码-{error_code}-{error_msg}")
                return False
        except Exception as e:
            logger.error(f"获取签到信息异常: {e}")
            return False

    def get_growth_sign(self):
        """执行签到"""
        logger.info("开始执行签到...")

        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/sign"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        data = {"sign_cyclic": True}
        try:
            response = requests.post(url=url, json=data, params=querystring, timeout=10)

            logger.debug(f"API 请求：POST {url} {response.status_code}")
            logger.debug(f"响应：{response.text[:300]}")

            response_data = response.json()
            if response_data.get("data"):
                # 签到成功，返回奖励
                reward = response_data["data"]["sign_daily_reward"]
                logger.info(f"签到成功，获得奖励: {self.convert_bytes(reward)}")
                return True, reward, False
            else:
                # 检查是否是重复签到
                message = response_data.get("message", "")
                if "repeat" in message.lower():
                    # 今日已签到
                    logger.info("今日已签到")
                    return True, 0, True
                else:
                    # 其他错误
                    error_msg = response_data.get("message", "未知错误")
                    logger.error(f"签到失败: {error_msg}")
                    return False, error_msg, False
        except Exception as e:
            logger.error(f"签到请求异常: {e}")
            return False, f"请求异常: {e}", False

    def do_sign(self, index):
        """执行签到并返回统一格式的通知"""
        logger.info(f"开始处理账号{index}...")

        # 检查必要参数
        required_params = ['kps', 'sign', 'vcode']
        missing_params = [p for p in required_params if not self.param.get(p)]
        if missing_params:
            username = self.param.get('user', f'账号{index}')
            error_msg = f"Cookie缺少必要参数: {', '.join(missing_params)}。请确保Cookie包含kps、sign、vcode三个参数"
            logger.error(error_msg)
            return username, {}, f"❌ {error_msg}", False

        # 获取用户名
        username = self.param.get('user', f'账号{index}')

        # 直接执行签到
        sign_success, sign_result, already_signed = self.get_growth_sign()

        # 无论签到成功或失败，都获取最新账号信息
        growth_info = self.get_growth_info()
        if not growth_info:
            logger.error("获取账号信息失败，Cookie可能已过期")
            return username, {}, "❌ 获取账号信息失败，Cookie可能已过期", False

        # 构建账号信息
        is_vip = growth_info.get('88VIP', False)
        vip_status = "88VIP" if is_vip else "普通用户"
        total_capacity = self.convert_bytes(growth_info.get('total_capacity', 0))

        sign_reward_capacity = "0B"
        if "sign_reward" in growth_info.get('cap_composition', {}):
            sign_reward_capacity = self.convert_bytes(growth_info['cap_composition']['sign_reward'])

        extra_info = {
            'vip_status': vip_status,
            'total_capacity': total_capacity,
            'sign_reward_capacity': sign_reward_capacity
        }

        logger.debug(f"账号信息: {vip_status}, 总容量: {total_capacity}, 签到累计: {sign_reward_capacity}")

        # 签到失败
        if not sign_success:
            logger.error(f"账号{index}签到失败: {sign_result}")
            return username, extra_info, f"签到失败：{sign_result}", False

        # 签到成功或今日已签到，获取签到进度
        cap_sign = growth_info.get('cap_sign', {})
        progress = cap_sign.get('sign_progress', 0)
        target = cap_sign.get('sign_target', 0)

        if already_signed:
            # 今日已签到
            reward = self.convert_bytes(cap_sign.get('sign_daily_reward', 0))
            sign_msg = f"今日已签到，获得 {reward}，连签进度 {progress}/{target}"
            logger.info(f"账号{index}: {sign_msg}")
        else:
            # 刚刚签到成功
            reward = self.convert_bytes(sign_result)
            sign_msg = f"签到成功，获得 {reward}，连签进度 {progress}/{target}"
            logger.info(f"账号{index}: {sign_msg}")

        return username, extra_info, sign_msg, True

def main():
    """主函数"""
    logger.info("开始获取环境变量...")
    QUARK_COOKIE = get_env()

    logger.info(f"检测到共 {len(QUARK_COOKIE)} 个夸克账号")

    success_count = 0
    fail_count = 0

    for i, cookie in enumerate(QUARK_COOKIE):
        logger.info(f"\n==== 账号{i + 1} 开始签到 ====")

        # 执行签到
        nickname, extra_info, sign_msg, is_success = Quark(cookie).do_sign(i + 1)

        if is_success:
            success_count += 1
            logger.info(f"{nickname}: {sign_msg}")
        else:
            fail_count += 1
            logger.error(f"{nickname}: {sign_msg}")

        # 统一通知格式
        notify_content = f"""🌐 域名：pan.quark.cn

👤 账号{i + 1}：
📱 用户：{nickname}"""

        # 添加额外信息（如果有）
        if extra_info:
            notify_content += f"""
👑 类别：{extra_info.get('vip_status', '未知')}
💾 总容量：{extra_info.get('total_capacity', '未知')}
📦 签到累计：{extra_info.get('sign_reward_capacity', '未知')}"""

        notify_content += f"""
📝 签到：{sign_msg}
⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        # 发送单个账号通知
        status = "成功" if is_success else "失败"
        if hadsend:
            try:
                send(f'[夸克网盘]签到{status}', notify_content)
                logger.info('通知推送成功')
            except Exception as e:
                logger.error(f'通知推送失败: {e}')
        else:
            logger.info(f'签到{status}')
            logger.debug(notify_content)

        # 多账号间随机等待
        if i < len(QUARK_COOKIE) - 1:
            delay = random.uniform(3, 8)
            logger.info(f"随机等待 {delay:.1f} 秒后处理下一个账号...")
            time.sleep(delay)

    # 发送汇总通知（仅多账号时）
    if len(QUARK_COOKIE) > 1:
        logger.info("\n==== 开始生成汇总通知 ====")
        summary = f"""🌐 域名：pan.quark.cn

📊 签到汇总：
✅ 成功：{success_count}个
❌ 失败：{fail_count}个
📈 成功率：{success_count/len(QUARK_COOKIE)*100:.1f}%
⏰ 完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        if hadsend:
            try:
                send('[夸克网盘]签到汇总', summary)
                logger.info('汇总通知推送成功')
            except Exception as e:
                logger.error(f'汇总通知推送失败: {e}')
        else:
            logger.info('签到汇总')
            logger.debug(summary)

    logger.info(f"\n==== 所有账号签到完成 - 成功{success_count}/{len(QUARK_COOKIE)} ====")
    return success_count

if __name__ == "__main__":
    logger.info(f"==== 夸克网盘签到开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====")

    logger.info("----------夸克网盘开始尝试签到----------")
    main()
    logger.info("----------夸克网盘签到执行完毕----------")
    logger.info(f"==== 夸克签到完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====")
