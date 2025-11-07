"""
cron "13 18 * * *" script-path=xxx.py,tag=匹配cron用
new Env('夸克签到')
"""
import os
import re
import sys
import time
import random
import requests
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

    print(f"夸克签到需要等待 {format_time_remaining(delay_seconds)}")

    remaining = delay_seconds
    while remaining > 0:
        if remaining <= 10 or remaining % 10 == 0:
            print(f"倒计时: {format_time_remaining(remaining)}")

        sleep_time = 1 if remaining <= 10 else min(10, remaining)
        time.sleep(sleep_time)
        remaining -= sleep_time

def get_env():
    """获取环境变量"""
    if "QUARK_COOKIE" in os.environ:
        cookie_list = re.split('\n|&&', os.environ.get('QUARK_COOKIE'))
        # 过滤空字符串
        cookie_list = [c.strip() for c in cookie_list if c.strip()]
    else:
        print('❌未添加QUARK_COOKIE变量')
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
        user_data = {}
        for item in cookie.replace(" ", "").split(';'):
            if item and '=' in item:
                key, value = item.split('=', 1)
                user_data[key] = value
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
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        try:
            response = requests.get(url=url, params=querystring, timeout=10).json()
            if response.get("data"):
                return response["data"]
            else:
                # 记录详细错误信息
                error_msg = response.get("message", "未知错误")
                error_code = response.get("code", "")
                print(f"❌ API返回错误: [{error_code}] {error_msg}")
                return False
        except Exception as e:
            print(f"❌ 获取签到信息异常: {e}")
            return False

    def get_growth_sign(self):
        """执行签到"""
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
            response = requests.post(url=url, json=data, params=querystring, timeout=10).json()
            if response.get("data"):
                # 签到成功，返回奖励
                return True, response["data"]["sign_daily_reward"], False
            else:
                # 检查是否是重复签到
                message = response.get("message", "")
                if "repeat" in message.lower():
                    # 今日已签到
                    return True, 0, True
                else:
                    # 其他错误
                    return False, response.get("message", "未知错误"), False
        except Exception as e:
            return False, f"请求异常: {e}", False

    def do_sign(self, index):
        """执行签到并返回统一格式的通知"""
        # 检查必要参数
        required_params = ['kps', 'sign', 'vcode']
        missing_params = [p for p in required_params if not self.param.get(p)]
        if missing_params:
            username = self.param.get('user', f'账号{index}')
            return username, {}, f"❌ Cookie缺少必要参数: {', '.join(missing_params)}。请确保Cookie包含kps、sign、vcode三个参数", False

        # 获取用户名
        username = self.param.get('user', f'账号{index}')

        # 直接执行签到
        sign_success, sign_result, already_signed = self.get_growth_sign()

        # 无论签到成功或失败，都获取最新账号信息
        growth_info = self.get_growth_info()
        if not growth_info:
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

        # 签到失败
        if not sign_success:
            return username, extra_info, f"签到失败：{sign_result}", False

        # 签到成功或今日已签到，获取签到进度
        cap_sign = growth_info.get('cap_sign', {})
        progress = cap_sign.get('sign_progress', 0)
        target = cap_sign.get('sign_target', 0)

        if already_signed:
            # 今日已签到
            reward = self.convert_bytes(cap_sign.get('sign_daily_reward', 0))
            sign_msg = f"今日已签到，获得 {reward}，连签进度 {progress}/{target}"
        else:
            # 刚刚签到成功
            reward = self.convert_bytes(sign_result)
            sign_msg = f"签到成功，获得 {reward}，连签进度 {progress}/{target}"

        return username, extra_info, sign_msg, True

def main():
    """主函数"""
    QUARK_COOKIE = get_env()

    print(f"✅ 检测到共 {len(QUARK_COOKIE)} 个夸克账号\n")

    success_count = 0
    fail_count = 0

    for i, cookie in enumerate(QUARK_COOKIE):
        print(f"\n==== 账号{i + 1} 开始签到 ====")

        # 执行签到
        nickname, extra_info, sign_msg, is_success = Quark(cookie).do_sign(i + 1)

        if is_success:
            success_count += 1
            print(f"✅ {nickname}: {sign_msg}")
        else:
            fail_count += 1
            print(f"❌ {nickname}: {sign_msg}")

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
                print('✅ 通知推送成功')
            except Exception as e:
                print(f'❌ 通知推送失败: {e}')
        else:
            print(f'📢 [夸克网盘]签到{status}')
            print(notify_content)

        # 多账号间随机等待
        if i < len(QUARK_COOKIE) - 1:
            delay = random.uniform(3, 8)
            print(f"⏱️  随机等待 {delay:.1f} 秒后处理下一个账号...")
            time.sleep(delay)

    # 发送汇总通知（仅多账号时）
    if len(QUARK_COOKIE) > 1:
        summary = f"""🌐 域名：pan.quark.cn

📊 签到汇总：
✅ 成功：{success_count}个
❌ 失败：{fail_count}个
📈 成功率：{success_count/len(QUARK_COOKIE)*100:.1f}%
⏰ 完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        if hadsend:
            try:
                send('[夸克网盘]签到汇总', summary)
                print('✅ 汇总通知推送成功')
            except Exception as e:
                print(f'❌ 汇总通知推送失败: {e}')
        else:
            print(f'📢 [夸克网盘]签到汇总')
            print(summary)

    print(f"\n==== 所有账号签到完成 - 成功{success_count}/{len(QUARK_COOKIE)} ====")
    return success_count

if __name__ == "__main__":
    print(f"==== 夸克网盘签到开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====")

    # 随机延迟（可选）
    if random_signin:
        delay_seconds = random.randint(0, max_random_delay)
        if delay_seconds > 0:
            print(f"随机模式: 延迟 {format_time_remaining(delay_seconds)} 后签到")
            wait_with_countdown(delay_seconds)

    print("----------夸克网盘开始尝试签到----------")
    main()
    print("----------夸克网盘签到执行完毕----------")
    print(f"==== 夸克签到完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====")
