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
from datetime import datetime, timedelta

# ---------------- 统一通知模块加载（和NodeSeek一样）----------------
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

#推送函数（修改为使用notify.py）
def Push(contents):
    """修改推送函数使用notify.py（保持原始调用方式）"""
    if hadsend:
        try:
            send('夸克签到', contents)
            print('✅ notify.py推送成功')
        except Exception as e:
            print(f'❌ notify.py推送失败: {e}')
    else:
        print(f'📢 夸克签到')
        print(f'📄 {contents}')

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

# 获取环境变量
def get_env():
    # 判断 QUARK_COOKIE是否存在于环境变量
    if "QUARK_COOKIE" in os.environ:
        # 读取系统变量以 \n 或 && 分割变量
        cookie_list = re.split('\n|&&',os.environ.get('QUARK_COOKIE') ) #os.environ.get('QUARK_COOKIE')
    else:
        # 标准日志输出
        print('❌未添加QUARK_COOKIE变量')
        # 脚本退出
        sys.exit(0)

    return cookie_list

class Quark:
    def __init__(self, cookie):
        self.cookie = cookie

    def get_growth_info(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
        querystring = {"pr": "ucpro", "fr": "pc", "uc_param_str": ""}
        headers = {
            "content-type": "application/json",
            "cookie": self.cookie
        }
        response = requests.get(url=url, headers=headers, params=querystring).json()
        # 检查data是否存在且包含必要字段
        if response.get("data") and response["data"].get("cap_sign"):
            return response["data"]
        else:
            return False

    def get_growth_sign(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/sign"
        querystring = {"pr": "ucpro", "fr": "pc", "uc_param_str": ""}
        payload = {"sign_cyclic": True}
        headers = {
            "content-type": "application/json",
            "cookie": self.cookie
        }
        response = requests.post(url=url, json=payload, headers=headers, params=querystring).json()
        if response.get("data"):
            return True, response["data"]["sign_daily_reward"]
        else:
            return False, response["message"]

    def get_account_info(self):
        url = "https://pan.quark.cn/account/info"
        querystring = {"fr": "pc", "platform": "pc"}
        headers = {
            "content-type": "application/json",
            "cookie": self.cookie
        }
        response = requests.get(url=url, headers=headers, params=querystring).json()
        if response.get("data"):
            return response["data"]
        else:
            return False

    def do_sign(self, index):
        """执行签到并返回统一格式的通知"""
        # 验证账号
        account_info = self.get_account_info()
        if not account_info:
            return f"账号{index}", "❌ 该账号登录失败，cookie无效", False

        nickname = account_info.get('nickname', f'账号{index}')

        # 每日领空间
        growth_info = self.get_growth_info()
        if not growth_info:
            return nickname, "❌ 获取签到信息失败", False

        # 检查是否已签到
        if growth_info["cap_sign"]["sign_daily"]:
            reward_mb = int(growth_info['cap_sign']['sign_daily_reward'] / 1024 / 1024)
            sign_msg = f"今日已签到，获得 {reward_mb}MB，连签进度 {growth_info['cap_sign']['sign_progress']}/{growth_info['cap_sign']['sign_target']}"
            return nickname, sign_msg, True
        else:
            # 执行签到
            sign, sign_return = self.get_growth_sign()
            if sign:
                reward_mb = int(sign_return / 1024 / 1024)
                sign_msg = f"签到成功，获得 {reward_mb}MB，连签进度 {growth_info['cap_sign']['sign_progress'] + 1}/{growth_info['cap_sign']['sign_target']}"
                return nickname, sign_msg, True
            else:
                return nickname, f"签到失败：{sign_return}", False

def main():
    global QUARK_COOKIE

    QUARK_COOKIE = get_env()

    print(f"✅ 检测到共 {len(QUARK_COOKIE)} 个夸克账号\n")

    success_count = 0
    fail_count = 0

    for i, cookie in enumerate(QUARK_COOKIE):
        print(f"\n==== 账号{i + 1} 开始签到 ====")

        # 执行签到
        nickname, sign_msg, is_success = Quark(cookie).do_sign(i + 1)

        if is_success:
            success_count += 1
            print(f"✅ {nickname}: {sign_msg}")
        else:
            fail_count += 1
            print(f"❌ {nickname}: {sign_msg}")

        # 统一通知格式
        notify_content = f"""🌐 域名：pan.quark.cn

👤 账号{i + 1}：
📱 用户：{nickname}
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
            signin_time = datetime.now() + timedelta(seconds=delay_seconds)
            print(f"随机模式: 延迟 {format_time_remaining(delay_seconds)} 后签到")
            print(f"预计签到时间: {signin_time.strftime('%H:%M:%S')}")
            wait_with_countdown(delay_seconds)
    
    print("----------夸克网盘开始尝试签到----------")
    main()
    print("----------夸克网盘签到执行完毕----------")
    print(f"==== 夸克签到完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====")
