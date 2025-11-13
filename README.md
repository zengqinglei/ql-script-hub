# QL Script Hub

> 🚀 个人青龙面板脚本库 - 签到、薅羊毛一站式解决方案

[![GitHub stars](https://img.shields.io/github/stars/agluo/ql-script-hub?style=flat-square)](https://github.com/agluo/ql-script-hub/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/agluo/ql-script-hub?style=flat-square)](https://github.com/agluo/ql-script-hub/network)
[![GitHub issues](https://img.shields.io/github/issues/agluo/ql-script-hub?style=flat-square)](https://github.com/agluo/ql-script-hub/issues)
[![License](https://img.shields.io/github/license/agluo/ql-script-hub?style=flat-square)](https://github.com/agluo/ql-script-hub/blob/main/LICENSE)

## 📋 项目简介

QL Script Hub 是一个专为青龙面板打造的综合性脚本库，提供签到、薅羊毛等多种类型的自动化脚本。所有脚本均经过测试，确保稳定可靠。

## ✨ 功能特性

- 🎯 **多样化脚本** - 涵盖签到、薅羊毛、监控等多种场景
- 🔧 **易于配置** - 统一的配置文件格式，简单易懂
- 📦 **模块化设计** - 清晰的目录结构，便于管理和扩展
- 🛡️ **安全可靠** - 所有脚本均经过测试，保证安全性
- 📝 **详细文档** - 每个脚本都有详细的使用说明
- 🔄 **持续更新** - 定期更新维护，修复问题和添加新功能

## 📁 目录结构

```
ql-script-hub/
├── README.md              # 项目说明文档
├── LICENSE                # 开源许可证
├── aliyunpan_signin.py    # 阿里云盘签到脚本
├── agentrouter_checkin.py # AgentRouter签到脚本
├── anyrouter_checkin.py   # AnyRouter签到脚本
├── baidu_signin.py        # 百度网盘签到
├── enshan_checkin.py      # 恩山论坛签到脚本
├── nodeseek_checkin.py    # nodeseek签到脚本
├── ikuuu_checkin.py       # ikuuu签到
├── nga_checkin.py         # NGA论坛签到
├── ty_netdisk_checkin.py  # 天翼云盘签到
├── quark_signin.py        # 夸克网盘签到脚本
├── SFSU_checkin.py        # 顺丰速运签到脚本
├── smzdm_checkin.py       # 什么值得买签到脚本
├── deepflood_checkin.py   # deepflood签到脚本
├── leaflow_checkin.py     # leaflow签到脚本
├── youdaoyun_checkin.py   # 有道云笔记签到脚本
└── tieba_checkin.py       # 贴吧签到脚本
```

## 🚀 快速开始

本项目支持两种运行方式：

- **方式一：青龙面板** - 传统方式，功能完整，推荐自建服务器用户
- **方式二：GitHub Actions** - 无需服务器，完全免费，推荐个人用户

---

## 🤖 方式一：GitHub Actions 自动运行（推荐）

### ✨ 功能特性

- ✅ **完全免费** - 使用 GitHub 免费额度，无需自建服务器
- ✅ **自动定时** - 每天北京时间 8:00 自动运行
- ✅ **支持多选** - 可选择运行特定脚本或全部脚本
- ✅ **智能判断** - 自动跳过未配置环境变量的脚本
- ✅ **完整通知** - 支持 Server酱、企业微信等多种推送方式
- ✅ **兼容青龙** - 100% 兼容青龙面板环境变量配置
- ✅ **自动更新** - 可配置自动更新 Token（如阿里云盘）

### 📋 快速开始

#### 1. Fork 本仓库

点击页面右上角的 **Fork** 按钮，将本仓库复制到你的账号下。

#### 2. 启用 GitHub Actions

1. 进入你 Fork 的仓库
2. 点击 **Actions** 标签
3. 点击 **I understand my workflows, go ahead and enable them**

#### 3. 配置 GitHub Secrets

进入 **Settings** > **Secrets and variables** > **Actions** > **New repository secret**

**必配项（推荐）：**

| 变量名 | 说明 | 示例值 |
|-------|------|-------|
| `PUSH_KEY` | Server酱推送Key | `SCT300842T...` |
| `QYWX_KEY` | 企业微信机器人Key | `5036ccf4-7f42...` |
| `PRIVACY_MODE` | 隐私模式（日志脱敏） | `true` |

**按需配置（根据你要使用的服务）：**

<details>
<summary>点击展开查看所有支持的环境变量</summary>

| 服务 | 环境变量 | 说明 |
|-----|---------|------|
| iKuuu | `IKUUU_EMAIL`, `IKUUU_PASSWD` | 登录邮箱和密码 |
| Leaflow | `LEAFLOW_COOKIE` | Cookie（JSON数组） |
| 阿里云盘 | `ALIYUN_REFRESH_TOKEN` | refresh_token |
| AnyRouter | `ANYROUTER_ACCOUNTS` | 账号配置（JSON） |
| AgentRouter | `AGENTROUTER_ACCOUNTS` | Linux.do账号配置（JSON） |
| 百度网盘 | `BAIDU_COOKIE` | Cookie |
| 夸克网盘 | `QUARK_COOKIE` | Cookie |
| 有道云笔记 | `YOUDAO_COOKIE` | Cookie |
| NodeSeek | `NODESEEK_COOKIE` | Cookie |
| DeepFlood | `DEEPFLOOD_COOKIE` | Cookie |
| NGA | `NGA_COOKIE` | Cookie |
| 百度贴吧 | `TIEBA_COOKIE` | Cookie |
| 什么值得买 | `SMZDM_COOKIE` | Cookie |
| 天翼云盘 | `TY_NETDISK_COOKIE` | Cookie |
| 顺丰速运 | `SFSU_COOKIE` | Cookie |
| 恩山论坛 | `ENSHAN_COOKIE` | Cookie |

详细配置方法见下方"获取方式说明"章节。

</details>

#### 4. 手动触发测试

1. 进入 **Actions** > **签到任务**
2. 点击 **Run workflow**
3. 在输入框中填写要运行的脚本：
   - **留空或 `all`**：自动运行所有已配置的脚本
   - **单个脚本**：如 `ikuuu`
   - **多个脚本**：如 `ikuuu,leaflow,aliyunpan`（逗号分隔）
4. 点击绿色的 **Run workflow** 按钮

#### 5. 查看运行日志

1. 进入 **Actions** 标签
2. 点击最近的 workflow 运行记录
3. 展开 **运行签到脚本** 查看详细日志

### 🎯 智能运行说明

**默认行为（`all` 模式）：**
- 自动检测每个脚本所需的环境变量
- 只运行已配置环境变量的脚本
- 跳过未配置的脚本

**示例输出：**
```
📋 输入的脚本: all
⏭️  跳过 ikuuu: 未配置所需环境变量 (IKUUU_EMAIL IKUUU_PASSWD)
🚀 开始执行: leaflow
✅ leaflow 执行成功
🚀 开始执行: aliyunpan
✅ aliyunpan 执行成功
```

### ⏰ 定时任务说明

**默认执行时间：** 每天北京时间 8:00（UTC 0:00）

**修改执行时间：** 编辑 `.github/workflows/checkin.yml` 中的 cron 表达式

```yaml
schedule:
  - cron: '0 0 * * *'  # UTC 0:00 = 北京 8:00
  - cron: '0 16 * * *'  # UTC 16:00 = 北京 0:00
```

### 🔄 Token 自动更新（高级功能）

某些服务（如阿里云盘）的 Token 会定期刷新，在 GitHub Actions 中提供两种方案：

#### 方案一：自动更新（推荐）

**优点：** 完全自动化，无需人工干预
**缺点：** 需要额外配置 PAT

**配置步骤：**

1. **创建 GitHub Personal Access Token**
   - 访问 https://github.com/settings/tokens
   - 点击 **Generate new token (classic)**
   - **Note**: `ql-script-hub-auto-update`
   - **Expiration**: 90 days 或 No expiration
   - **Scopes**: 勾选 ✅ **repo**（完整勾选）
   - 复制生成的 token

2. **配置 GH_PAT Secret**
   - 进入仓库 **Settings** > **Secrets** > **Actions**
   - 添加 Secret：
     - Name: `GH_PAT`
     - Value: 粘贴刚才的 token

3. **验证自动更新**
   - 运行一次 workflow
   - 查看日志中是否有 "✅ Secret 更新成功"

#### 方案二：手动更新（简单）

**优点：** 配置简单，更安全
**缺点：** 需要人工更新（约 3-6 个月一次）

**使用方法：**
- 不配置 `GH_PAT`
- 当 Token 更新时，通知消息会包含新 Token
- 收到通知后，手动更新 GitHub Secret

### ⚠️ 注意事项

1. **仓库活跃度**：如果 60 天无提交，定时任务会被禁用
2. **AgentRouter 限制**：无头模式成功率较低（GitHub Actions 环境限制）
3. **Cookie 有效期**：定期检查 Cookie 是否过期
4. **定时任务延迟**：GitHub Actions 可能有 5-10 分钟延迟

---

## 🐉 方式二：青龙面板运行

### 环境要求

- 青龙面板 2.10+
- Node.js 14+
- **⚠️ AgentRouter 特殊要求**：
  - CPU > 500m（推荐 1 核心）
  - 内存 > 1024MB（推荐 2GB）
  - 需安装 Playwright + Chromium 浏览器

### 安装步骤

1. **拉取仓库**
   ```bash
   # 在青龙面板订阅管理中添加订阅
   # 订阅地址：https://github.com/zengqinglei/ql-script-hub.git
   ```
  <img width="774" height="1112" alt="image" src="https://github.com/user-attachments/assets/de6cf07f-7af2-42b9-8321-c2ccc542820b" />

2. **安装Python依赖**
   - 青龙面板 → 依赖管理 → Python3
   - 添加依赖：`PyExecJS` (anyrouter_checkin.py 脚本依赖，用于处理WAF挑战)
   - 点击安装

   **使用 AgentRouter 脚本需额外安装：**
   - 青龙面板 → 依赖管理 → Python3 → 添加依赖：`playwright`
   - 安装完成后，进入青龙容器执行：
     ```bash
     # 进入容器
     docker exec -it qinglong bash

     # 安装 Chromium 浏览器
     playwright install chromium
     playwright install-deps chromium

     # 验证安装
     playwright --version
     ```

   > **⚠️ 资源要求说明：**
   > - AgentRouter 使用 Playwright 自动化浏览器进行 Linux.do 认证
   > - Chromium 浏览器最低要求：CPU 500m + 内存 1GB
   > - 推荐配置：CPU 1核心 + 内存 2GB，成功率更高
   > - **如果资源不足**：建议使用 GitHub Actions 方式（无需安装浏览器）

3. **配置环境变量（复用青龙通知模块）**

   
| 变量名 | 说明 | 是否必需 | 示例值 | 备注 |
|--------|------|----------|--------|------|
| `TG_BOT_TOKEN` | Telegram机器人Token | 推荐 | `1234567890:AAG9rt-6RDaaX0HBLZQq0laNOh898iFYaRQ` | 获取方式见下方说明 |
| `TG_USER_ID` | Telegram用户ID | 推荐 | `1434078534` | 获取方式见下方说明 |
| `PUSH_KEY` | Server酱推送Key | 可选 | `SCTxxxxxxxxxxxxxxxxxxxxx` | 微信推送，访问 sct.ftqq.com 获取 |
| `PUSH_PLUS_TOKEN` | Push+推送Token | 可选 | `xxxxxxxxxxxxxxxxxx` | 微信推送，访问 pushplus.plus 获取 |
| `DD_BOT_TOKEN` | 钉钉机器人Token | 可选 | `xxxxxxxxxxxxxxxxxx` | 钉钉群机器人 |
| `DD_BOT_SECRET` | 钉钉机器人密钥 | 可选 | `xxxxxxxxxxxxxxxxxx` | 钉钉群机器人密钥（可选） |
| `BARK_PUSH` | Bark推送地址 | 可选 | `https://api.day.app/your_key/` | iOS Bark推送 |
| `QYWX_KEY` | 企业微信机器人Key | 可选 | `5036ccf4-7f42-4d43-a333-bffa10f35369` | 企业微信群机器人推送 |

#### 🏔️ 恩山论坛签到配置

| 变量名 | 说明 | 是否必需 | 示例值 | 备注 |
|--------|------|----------|--------|------|
| `enshan_cookie` | 恩山论坛Cookie | **必需** | `完整的Cookie字符串` | 单账号Cookie |

#### 📱 NodeSeek 签到配置

| 变量名 | 说明 | 是否必需 | 示例值 | 备注 |
|--------|------|----------|--------|------|
| `NODESEEK_COOKIE` | NodeSeek网站Cookie | **必需** | `cookie1&cookie2&cookie3` | 多账号用`&`分隔 |
| `NS_RANDOM` | 签到随机参数 | 可选 | `true` | 默认值，通常无需修改 |

#### ☁️ 夸克网盘签到配置

| 变量名 | 说明 | 是否必需 | 示例值 | 备注 |
|--------|------|----------|--------|------|
| `QUARK_COOKIE` | 夸克网盘Cookie | **必需** | `cookie1&&cookie2` | 多账号用`&&`或回车分隔 |

#### 📦 顺丰速运签到配置

| 变量名 | 说明 | 是否必需 | 示例值 | 备注 |
|--------|------|----------|--------|------|
| `sfsyUrl` | 顺丰速运登录URL | **必需** | `https://mcs-mimp...` | 抓包获取，多账号换行 |

#### 百度贴吧签到配置

| 变量名 | 说明 | 是否必需 | 示例值 | 备注 |
|--------|------|----------|--------|------|
| `TIEBA_COOKIE` | 百度贴吧Cookie | **必需** | `BDUSS=xxxxxx; STOKEN=xxxxx...` | 完整的Cookie字符串，多账号换行 |

#### ☁️ 阿里云盘签到配置 

| 变量名 | 说明 | 是否必需 | 示例值 | 备注 |
|--------|------|----------|--------|------|
| `ALIYUN_REFRESH_TOKEN` | 阿里云盘refresh_token | **必需** | `crsh166bdfde4751a4c0...` | 多账号用`&`或换行分隔 |
| `AUTO_UPDATE_TOKEN` | 自动更新Token | 可选 | `true` | 默认`true`，自动维护token |
| `PRIVACY_MODE` | 隐私保护模式 | 可选 | `true` | 默认`true`，脱敏显示敏感信息 |

#### 🛒 什么值得买签到配置 

| 变量名 | 说明 | 是否必需 | 示例值 | 备注 |
|--------|------|----------|--------|------|
| `SMZDM_COOKIE` | 什么值得买Cookie | **必需** | `__ckguid==xxxxx; device_id=xxxxx...` | 完整Cookie，多账号换行分隔 |

#### ☁️ 百度网盘配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `BAIDU_COOKIE` | 网站Cookie | `BDUSS=xxx; STOKEN=xxx...` |
| `PRIVACY_MODE` | 隐私模式 | `true` |

#### 📡 ikuuu签到配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `IKUUU_EMAIL` | 登录邮箱 | `user@example.com` |
| `IKUUU_PASSWD` | 登录密码 | `password123` |

#### ☁️ 天翼云盘配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `TY_USERNAME` | 登录手机号 | `13812345678&13987654321` |
| `TY_PASSWORD` | 登录密码 | `password1&password2` |

#### 🎮 NGA论坛配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `NGA_CREDENTIALS` | UID,AccessToken | `12345678,abcdef...` |

#### 📱 deepflood签到配置

| 变量名 | 说明 | 是否必需 | 示例值 | 备注 |
|--------|------|----------|--------|------|
| `DEEPFLOOD_COOKIE` | NodeSeek网站Cookie | **必需** | `cookie1&cookie2&cookie3` | 多账号用`&`分隔 |
| `NS_RANDOM` | 签到随机参数 | 可选 | `true` | 默认值，通常无需修改 |

#### ☁ leaflow签到配置

| 变量名 | 说明 | 是否必需 | 示例值 | 备注 |
|--------|------|----------|--------|------|
| `LEAFLOW_COOKIE` | leaflow网站Cookie（JSON数组格式） | **必需** | `[{"leaflow_session":"xxx","remember_web_xxx":"yyy","XSRF-TOKEN":"zzz"}]` | JSON数组格式，支持多账号 |

#### 🌐 AnyRouter签到配置

| 变量名 | 说明 | 是否必需 | 示例值 | 备注 |
|--------|------|----------|--------|------|
| `ANYROUTER_ACCOUNTS` | AnyRouter账号配置（JSON数组格式） | **必需** | `[{"cookies":{"session":"xxx"},"api_user":"123"}]` | JSON数组格式，支持多账号 |
| `ANYROUTER_BASE_URL` | API基础地址 | 可选 | `https://q.quuvv.cn` | 默认`https://anyrouter.top` |
| `ANYROUTER_TIMEOUT` | 请求超时时间（秒） | 可选 | `60` | 默认30秒 |
| `ANYROUTER_VERIFY_SSL` | SSL证书验证 | 可选 | `false` | 默认`true` |
| `ANYROUTER_MAX_RETRIES` | 最大重试次数 | 可选 | `5` | 默认3次 |

#### 🌐 AgentRouter签到配置

| 变量名 | 说明 | 是否必需 | 示例值 | 备注 |
|--------|------|----------|--------|------|
| `AGENTROUTER_ACCOUNTS` | AgentRouter账号配置（JSON数组格式） | **必需** | 见下方详细说明 | JSON数组格式，支持多账号 |
| `BROWSER_HEADLESS` | 浏览器无头模式 | 可选 | `true` | 默认`true`，GitHub Actions 必须为 true |

**配置格式说明：**

`AGENTROUTER_ACCOUNTS` 是一个 JSON 数组，每个账号需要包含以下字段：

```json
[
  {
    "name": "账号名称（自定义）",
    "linux.do": {
      "username": "你的Linux.do登录邮箱",
      "password": "你的Linux.do登录密码"
    }
  }
]
```

**多账号示例：**

```json
[
  {
    "name": "账号1",
    "linux.do": {
      "username": "user1@example.com",
      "password": "password1"
    }
  },
  {
    "name": "账号2",
    "linux.do": {
      "username": "user2@example.com",
      "password": "password2"
    }
  }
]
```

**⚠️ 重要说明：**
- AgentRouter 使用 **Linux.do** 账号进行 OAuth 认证
- **必须提供** Linux.do 的登录邮箱和密码
- 脚本会自动使用 Playwright 浏览器完成登录认证流程
- 认证过程需要一定时间（约 30-60 秒）
- **无头模式**成功率较低，建议青龙面板用户使用有头模式（设置 `BROWSER_HEADLESS=false`）

#### 📓 有道云笔记签到配置

| 变量名 | 说明 | 是否必需 | 示例值 | 备注 |
|--------|------|----------|--------|------|
| `YOUDAO_COOKIE` | 有道云笔记Cookie | **必需** | 完整的Cookie字符串 | 单账号Cookie，多账号换行分隔 |

#### ⏰ 随机化配置（所有脚本共用）

| 变量名 | 说明 | 是否必需 | 示例值 | 备注 |
|--------|------|----------|--------|------|
| `RANDOM_SIGNIN` | 启用随机签到 | 可选 | `true` | `true`启用，`false`禁用 |
| `MAX_RANDOM_DELAY` | 随机延迟窗口（秒） | 可选 | `3600` | `3600`=1小时，`1800`=30分钟 |

---

## 🔧 获取方式说明

### 📱 Telegram配置获取
1. **创建机器人**: 与 [@BotFather](https://t.me/botfather) 对话，发送 `/newbot` 创建机器人
2. **获取Token**: 创建完成后会收到 `TG_BOT_TOKEN`
3. **获取用户ID**: 与 [@userinfobot](https://t.me/userinfobot) 对话获取 `TG_USER_ID`

### 🍪 Cookie获取方式

#### 恩山论坛 Cookie  
1. 浏览器访问 [恩山论坛](https://www.right.com.cn/FORUM/) 并登录
2. F12 开发者工具 → Network → 刷新页面
3. 找到请求头中的 `Cookie` 完整复制

#### NodeSeek Cookie
1. 浏览器访问 [nodeseek.com](https://www.nodeseek.com) 并登录
2. F12 开发者工具 → Network → 刷新页面
3. 找到请求头中的 `Cookie` 完整复制

#### Deepflood Cookie
1. 浏览器访问 [nodeseek.com](https://www.deepflood.com) 并登录
2. F12 开发者工具 → Network → 刷新页面
3. 找到请求头中的 `Cookie` 完整复制

#### 夸克网盘 Cookie
1. 使用**手机抓包工具**获取移动端Cookie（推荐 [ProxyPin](https://github.com/wanghongenpin/network_proxy_flutter)）
2. 打开手机抓包工具，访问夸克网盘签到页
3. 找到接口 `https://drive-m.quark.cn/1/clouddrive/capacity/growth/info` 的请求信息
4. 复制请求中的参数：`kps`、`sign` 和 `vcode`
5. 按以下格式组合Cookie：
   ```
   user=张三; kps=abcdefg; sign=hijklmn; vcode=111111111;
   ```
   - `user` 字段为用户名，可随意填写（用于日志区分）
   - `kps`、`sign`、`vcode` 为必需参数，从抓包中获取
6. 多账号配置：用 `&&` 或回车分隔
   ```
   user=账号1; kps=xxx; sign=yyy; vcode=zzz;&&user=账号2; kps=aaa; sign=bbb; vcode=ccc;
   ```

#### 顺丰速运 sfsyUrl
1. 顺丰APP绑定微信后，添加机器人发送"顺丰"
2. 打开小程序或APP-我的-积分，抓包以下URL之一:
   - `https://mcs-mimp-web.sf-express.com/mcs-mimp/share/weChat/shareGiftReceiveRedirect`
   - `https://mcs-mimp-web.sf-express.com/mcs-mimp/share/app/shareRedirect`
3. 抓取URL后，使用 [URL编码工具](https://www.toolhelper.cn/EncodeDecode/Url) 进行编码

#### 百度贴吧 Cookie
1. 浏览器访问 [tieba.baidu.com](https://tieba.baidu.com) 并登录
2. F12 开发者工具 → Network → 刷新页面  
3. 找到请求头中的完整 `Cookie` 复制
4. 确保包含 `BDUSS` 参数

#### 阿里云盘 refresh_token 
1. 浏览器访问 [阿里云盘网页版](https://www.aliyundrive.com/) 并登录
2. 按 `F12` 打开开发者工具 → `Application` 标签页
3. 左侧找到 `Local Storage` → `https://www.aliyundrive.com`
4. 找到 `token` 项，复制 `refresh_token` 的值

#### 什么值得买 Cookie 
1. 浏览器访问 [什么值得买](https://www.smzdm.com/) 并登录
2. 按 `F12` 打开开发者工具 → `Network` 标签页
3. 刷新页面，找到任意请求的 `Request Headers`
4. 复制完整的 `Cookie` 值

#### 百度网盘 Cookie 
1. 访问 [百度网盘](https://pan.baidu.com/) 登录
2. F12 → Network → 复制Cookie

#### Ikuuu 配置 
1. 在青龙面板中添加环境变量IKUUU_EMAIL（邮箱地址）
2. 在青龙面板中添加环境变量IKUUU_PASSWD（对应密码）
3. 多账号用英文逗号分隔: email1,email2
4. 密码顺序要与邮箱顺序对应

#### 天翼云盘配置 
1. 浏览器访问 [天翼云盘](https://e.dlife.cn/index.do) ，关闭设备锁
2. 在青龙面板中添加环境变量TY_USERNAME（手机号）
3. 在青龙面板中添加环境变量TY_PASSWD（对应密码）

#### leaflow配置（JSON数组格式）
1. 浏览器访问 [leaflow](https://leaflow.net/workspaces) 并登录
2. 按 F12 打开开发者工具 → Application（应用）标签页
3. 左侧找到 Cookies → https://leaflow.net
4. 复制以下三个 cookie 的完整值：
   - `leaflow_session`：会话token（通常以 eyJ 开头）
   - `remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d`：持久化登录token
   - `XSRF-TOKEN`：CSRF防护token
5. 将 cookie 字符串转换为 JSON 对象格式：
   - 字符串格式：`leaflow_session=xxx; remember_web_xxx=yyy; XSRF-TOKEN=zzz`
   - JSON格式：`{"leaflow_session":"xxx","remember_web_xxx":"yyy","XSRF-TOKEN":"zzz"}`
6. 组合成 JSON 数组格式设置到青龙面板环境变量 LEAFLOW_COOKIE：
   ```json
   [{"leaflow_session":"你的session值","remember_web_xxx":"你的remember值","XSRF-TOKEN":"你的token值"}]
   ```

#### 有道云笔记Cookie获取
1. 浏览器访问 [有道云笔记](https://note.youdao.com/) 并登录
2. 按 F12 打开开发者工具 → Network（网络）标签页
3. 刷新页面，找到任意请求
4. 查看请求的 Headers → Cookie：复制完整的 Cookie 值
5. Cookie示例：`__yadk_uid=xxx; YNOTE_SESS=xxx; YNOTE_PERS=xxx; ...`
6. 在青龙面板环境变量中设置 `YOUDAO_COOKIE`，值为完整的Cookie字符串
7. 多账号配置：每个Cookie单独一行，按顺序执行

**注意：**
- 必须包含 `YNOTE_PERS` 字段，脚本需要从中提取用户ID
- Cookie会定期过期，失效后需要重新获取
- 建议定期运行脚本避免Cookie失效

#### AnyRouter配置（JSON数组格式）
1. 浏览器访问 [AnyRouter](https://anyrouter.top) 并登录
2. 按 F12 打开开发者工具 → Network（网络）标签页
3. 刷新页面，找到任意 API 请求（如 `/api/user/self`）
4. 查看请求的 Headers：
   - **Cookies**：复制 Cookie 字段的值（如 `session=xxx; token=xxx`）
   - **new-api-user**：复制该请求头的值（这是你的 api_user ID）
5. 将 Cookie 字符串转换为 JSON 对象格式：
   - 字符串格式：`session=abc123; token=xyz789`
   - JSON格式：`{"session":"abc123","token":"xyz789"}`
6. 组合成 JSON 数组格式设置到青龙面板环境变量 ANYROUTER_ACCOUNTS：
   ```json
   [{"cookies":{"session":"你的session值","token":"你的token值"},"api_user":"你的api_user值"}]
   ```

**注意：**
- 必须使用 JSON 数组格式 `[{}]`
- JSON 格式必须使用双引号
- 多账号添加多个对象，用逗号分隔
- 脚本会自动处理 WAF 挑战，无需手动配置 WAF cookies

#### AgentRouter配置（JSON数组格式）

**与 AnyRouter 的重要区别：**
- AgentRouter 使用 **Linux.do OAuth 认证**，不需要抓包获取 cookies
- 只需要提供 Linux.do 的登录账号和密码即可
- 脚本会自动使用 Playwright 浏览器完成 OAuth 认证流程

**配置步骤：**

1. **准备 Linux.do 账号**
   - 访问 [Linux.do](https://linux.do) 注册账号（如果还没有）
   - 记录你的登录邮箱和密码

2. **配置环境变量**

   在青龙面板或 GitHub Secrets 中设置 `AGENTROUTER_ACCOUNTS`：

   ```json
   [
     {
       "name": "我的AgentRouter账号",
       "linux.do": {
         "username": "你的Linux.do登录邮箱",
         "password": "你的Linux.do登录密码"
       }
     }
   ]
   ```

3. **多账号配置示例**

   ```json
   [
     {
       "name": "账号1",
       "linux.do": {
         "username": "user1@example.com",
         "password": "password1"
       }
     },
     {
       "name": "账号2",
       "linux.do": {
         "username": "user2@example.com",
         "password": "password2"
       }
     }
   ]
   ```

**⚠️ 注意事项：**
- 必须安装 Playwright 和 Chromium 浏览器（青龙面板用户）
- 认证过程需要 30-60 秒，请耐心等待
- **青龙面板用户**：建议设置 `BROWSER_HEADLESS=false` 使用有头模式，成功率更高
- **GitHub Actions 用户**：只能使用无头模式，成功率较低（约 30-50%）
- 如果认证失败，可以多次重试
- **安全提示**：密码会存储在环境变量中，请确保环境安全

#### NGA论坛配置
1. 安装抓包工具并开启 HTTPS 解密，安装并信任证书 Android：HTTP Canary、HttpToolkit、mitmproxy、Charles; iOS：Stream、Charles
2. 将手机的网络代理指向抓包工具（或使用工具的本机 VPN/代理模式）
3. 打开 NGA 官方 App，确保已登录；在 App 内随便执行一个操作（进入首页/签到等）触发请求
4. 在抓包记录中找到对以下地址的 POST 请求： https://ngabbs.com/nuke.php
5. 打开该请求的请求体（Content-Type 一般是 application/x-www-form-urlencoded），复制以下参数的值：access_uid=你的UID;access_token=一串长字符串
7. 将上述两者按“UID,AccessToken”格式填写为环境变量 NGA_CREDENTIALS
   单账号示例：123456,abcdefg
   多账号用 & 分隔：123456,abcdefg&234567,hijklmn

---


## 🤝 贡献指南

欢迎贡献代码和提出建议！

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 📄 免责声明

- 本项目仅供学习交流使用，请勿用于商业用途
- 使用本项目所产生的任何问题，作者不承担任何责任
- 请遵守相关网站的使用条款和法律法规

## 📞 联系方式

- GitHub: [@agluo](https://github.com/agluo)
- Issues: [项目问题反馈](https://github.com/agluo/ql-script-hub/issues)

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源协议。

## ⭐ Star History

如果这个项目对你有帮助，请给个 Star ⭐️

[![Star History Chart](https://api.star-history.com/svg?repos=agluo/ql-script-hub&type=Date)](https://star-history.com/#agluo/ql-script-hub&Date)
