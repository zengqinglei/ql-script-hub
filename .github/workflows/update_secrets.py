#!/usr/bin/env python3
"""
GitHub Secrets 自动更新脚本
用于在 GitHub Actions 中自动更新环境变量（如 refresh_token）
"""
import os
import sys
import base64
import requests
from nacl import encoding, public


def encrypt_secret(public_key: str, secret_value: str) -> str:
    """使用仓库的公钥加密 secret"""
    public_key_obj = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key_obj)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def get_public_key(repo: str, token: str) -> tuple:
    """获取仓库的公钥"""
    url = f"https://api.github.com/repos/{repo}/actions/secrets/public-key"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data["key"], data["key_id"]
    else:
        raise Exception(f"获取公钥失败: {response.status_code} {response.text}")


def update_secret(repo: str, token: str, secret_name: str, secret_value: str):
    """更新 GitHub Secret"""
    try:
        # 获取公钥
        public_key, key_id = get_public_key(repo, token)

        # 加密 secret
        encrypted_value = encrypt_secret(public_key, secret_value)

        # 更新 secret
        url = f"https://api.github.com/repos/{repo}/actions/secrets/{secret_name}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "encrypted_value": encrypted_value,
            "key_id": key_id
        }

        response = requests.put(url, headers=headers, json=data)
        if response.status_code in [201, 204]:
            print(f"✅ Secret {secret_name} 更新成功")
            return True
        else:
            print(f"❌ Secret {secret_name} 更新失败: {response.status_code} {response.text}")
            return False

    except Exception as e:
        print(f"❌ 更新 Secret 异常: {e}")
        return False


def read_token_from_log(log_file: str, token_name: str) -> str:
    """从日志文件中读取新的 token"""
    if not os.path.exists(log_file):
        return None

    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            # 查找类似 "新Token: xxxx" 的行
            if token_name in line and ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    return parts[1].strip()
    return None


def main():
    """主函数"""
    # 获取环境变量
    github_token = os.getenv("GH_PAT")  # GitHub Personal Access Token
    github_repo = os.getenv("GITHUB_REPOSITORY")  # 格式: owner/repo

    if not github_token:
        print("⚠️ 未设置 GH_PAT，跳过自动更新 Secrets")
        return

    if not github_repo:
        print("❌ 未找到 GITHUB_REPOSITORY 环境变量")
        return

    print(f"📦 仓库: {github_repo}")
    print("🔄 开始检查需要更新的 Secrets...")

    # 检查是否有新的 ALIYUN_REFRESH_TOKEN
    new_aliyun_token = os.getenv("NEW_ALIYUN_REFRESH_TOKEN")
    if new_aliyun_token:
        print(f"🔍 检测到新的阿里云盘 refresh_token")
        update_secret(github_repo, github_token, "ALIYUN_REFRESH_TOKEN", new_aliyun_token)

    # 可以添加更多需要自动更新的 token
    # 例如：百度网盘、夸克网盘等

    print("✅ Secrets 检查完成")


if __name__ == "__main__":
    main()
