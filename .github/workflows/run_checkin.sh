#!/bin/bash
set -e  # 遇到错误立即退出

# 设置北京时区
export TZ=Asia/Shanghai

echo "=========================================="
echo "开始执行签到任务"
echo "当前时间: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "=========================================="

# 获取输入参数（默认为 all）
SCRIPT_NAME="${1:-all}"

# 根据选择确定要运行的脚本
if [ "$SCRIPT_NAME" = "all" ]; then
  SCRIPTS_INPUT="all"
  echo "运行模式: 所有脚本"
else
  SCRIPTS_INPUT="$SCRIPT_NAME"
  echo "运行模式: 单个脚本 - $SCRIPT_NAME"
fi

echo ""

# 定义函数：检查环境变量是否存在
check_env() {
  local env_name=$1
  if [ -n "${!env_name}" ]; then
    return 0
  else
    return 1
  fi
}

# 定义函数：检查脚本所需的环境变量是否已配置
check_script_env() {
  local script_name=$1
  shift
  local required_envs=("$@")

  for env in "${required_envs[@]}"; do
    if check_env "$env"; then
      return 0
    fi
  done
  return 1
}

# 定义函数：判断是否应该运行该脚本
should_run() {
  local script_name=$1

  if [ "$SCRIPTS_INPUT" = "all" ] || [ "$SCRIPTS_INPUT" = "ALL" ]; then
    return 0
  fi

  if echo ",$SCRIPTS_INPUT," | grep -q ",$script_name,"; then
    return 0
  fi

  return 1
}

# 定义函数：运行脚本
run_script() {
  local script_name=$1
  local script_file=$2
  shift 2
  local required_envs=("$@")

  if ! should_run "$script_name"; then
    return
  fi

  if [ ! -f "$script_file" ]; then
    echo "⚠️  脚本文件不存在: $script_file"
    return
  fi

  if [ "$SCRIPTS_INPUT" = "all" ] || [ "$SCRIPTS_INPUT" = "ALL" ]; then
    if ! check_script_env "$script_name" "${required_envs[@]}"; then
      echo "⚠️  跳过 $script_name: 未配置环境变量"
      return
    fi
  fi

  echo ""
  echo "=========================================="
  echo "▶️  开始执行: $script_name"
  echo "=========================================="

  if python "$script_file"; then
    echo "✅ $script_name 执行成功"
  else
    echo "❌ $script_name 执行失败（退出码: $?）"
  fi
}

# 执行各个签到脚本
run_script "ikuuu" "ikuuu_checkin.py" "IKUUU_EMAIL" "IKUUU_PASSWD"
run_script "leaflow" "leaflow_checkin.py" "LEAFLOW_COOKIE"
run_script "aliyunpan" "aliyunpan_checkin.py" "ALIYUN_REFRESH_TOKEN"
run_script "anyrouter" "anyrouter_checkin.py" "ANYROUTER_ACCOUNTS"
run_script "youdaoyun" "youdaoyun_checkin.py" "YOUDAO_COOKIE"
run_script "baiduwangpan" "baiduwangpan_checkin.py" "BAIDU_COOKIE"
run_script "quark" "quark_checkin.py" "QUARK_COOKIE"
run_script "nodeseek" "nodeseek_checkin.py" "NODESEEK_COOKIE"
run_script "deepflood" "deepflood_checkin.py" "DEEPFLOOD_COOKIE"
run_script "nga" "nga_checkin.py" "NGA_CREDENTIALS"
run_script "tieba" "tieba_checkin.py" "TIEBA_COOKIE"
run_script "smzdm" "smzdm_checkin.py" "SMZDM_COOKIE"
run_script "ty_netdisk" "ty_netdisk_checkin.py" "TY_USERNAME" "TY_PASSWORD"
run_script "sfsu" "sfsu_checkin.py" "SFSU_COOKIE"
run_script "enshan" "enshan_checkin.py" "ENSHAN_COOKIE"
run_script "agentrouter" "agentrouter_checkin.py" "AGENTROUTER_ACCOUNTS"

echo ""
echo "=========================================="
echo "✨ 所有签到任务执行完成"
echo "完成时间: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "=========================================="
