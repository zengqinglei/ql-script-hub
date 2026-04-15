# QL Script Hub

> 🚀 个人青龙面板脚本库 - 签到、薅羊毛一站式解决方案

[![GitHub stars](https://img.shields.io/github/stars/agluo/ql-script-hub?style=flat-square)](https://github.com/agluo/ql-script-hub/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/agluo/ql-script-hub?style=flat-square)](https://github.com/agluo/ql-script-hub/network)
[![GitHub issues](https://img.shields.io/github/issues/agluo/ql-script-hub?style=flat-square)](https://github.com/agluo/ql-script-hub/issues)
[![License](https://img.shields.io/github/license/agluo/ql-script-hub?style=flat-square)](https://github.com/agluo/ql-script-hub/blob/main/LICENSE)

## 📅 更新日志

- **2026-04-15**:
  - 整合 GemAI、AnyRouter、AgentRouter、996Coder 为统一脚本 `newapi_checkin.py`
  - 使用 `NEWAPI_ACCOUNTS` 单一环境变量管理所有 NewAPI 系站点账号
  - 认证方式通过账号字段自动判断，签到路径默认 fallback，支持按需覆盖

- **2026-02-01**: 
  - 修复阿里云盘 Token 自动更新机制，支持 GitHub Actions Secrets 自动同步
  - 新增 `NO_PROXY_SCRIPTS` 配置，支持指定脚本直连（绕过代理）
  - iKuuu 签到增加 `IKUUU_DOMAIN` 自定义域名配置
  - 修复 GemAI/AnyRouter 签到脚本在"已签到"状态下的误报问题

## 📋 项目简介

QL Script Hub 是一个专为青龙面板打造的综合性脚本库，提供签到、薅羊毛等多种类型的自动化脚本。所有脚本均经过测试，确保稳定可靠。

## 🚀 快速开始

本项目支持两种运行方式：

- **方式一：青龙面板** - 传统方式，功能完整，推荐自建服务器用户
- **方式二：GitHub Actions** - 无需服务器，完全免费，推荐个人用户

---

## 🤖 方式一：GitHub Actions 自动运行（推荐）

### 📋 快速开始

#### 1. Fork 本仓库

点击页面右上角的 **Fork** 按钮，将本仓库复制到你的账号下。

#### 2. 配置 GitHub Secrets

进入 **Settings** > **Secrets and variables** > **Actions** > **New repository secret**

根据你要使用的服务，参考下方"环境变量配置"章节添加对应的 Secret。

#### 3. 启用 GitHub Actions

1. 进入你 Fork 的仓库
2. 点击 **Actions** 标签
3. 点击 **I understand my workflows, go ahead and enable them**

#### 4. 手动触发测试

进入 **Actions** > **签到任务** > **Run workflow**：

**选择要运行的脚本**：
- `all`（默认）：运行所有已配置的脚本
- 或选择单个脚本：`ikuuu`、`aliyunpan`、`agentrouter` 等

**说明：** 自动检测环境变量，只运行已配置的脚本。

### ⏰ 定时任务

**默认执行时间：** 每天北京时间 8:30 和 17:30（UTC 0:30 和 9:30）

**修改时间：** 编辑 `.github/workflows/checkin.yml` 中的 cron 表达式

### 🔄 Token 自动更新（可选）

<details>
<summary>点击展开配置</summary>

某些服务（如阿里云盘）的 Token 会定期刷新，提供两种方案：

**方案一：自动更新**
1. 访问 https://github.com/settings/tokens 创建 Personal Access Token
2. Scopes 勾选 **repo**，复制生成的 token
3. 在仓库中添加 Secret: `GH_PAT`（值为刚才的 token）

**方案二：手动更新**
- 不配置 `GH_PAT`，通知消息会包含新 Token
- 收到通知后，手动更新 GitHub Secret

</details>

### ⚠️ 注意事项

- **仓库活跃度**：60 天无提交，定时任务会被禁用
- **定时任务延迟**：可能有 5-10 分钟延迟
- **Cloudflare WARP**：已集成 WARP 绕过部分网站的 IP 封锁限制

---

## 🐉 方式二：青龙面板运行

### 环境要求

- 青龙面板 2.10+
- 最小配置：CPU > 100m, 内存 > 384MB
- 推荐配置：CPU >= 1000m, 内存 >= 2GB

### 安装步骤

1. **拉取仓库**
   - 青龙面板 → 订阅管理 → 添加订阅
   - 订阅地址：`https://github.com/zengqinglei/ql-script-hub.git`
   - 点击保存并运行

2. **安装 Python 依赖**

   进入青龙面板 → 依赖管理 → Python3：

   - **公共依赖**：`requests`
   - **newapi 签到（Cookie 模式）依赖**：`PyExecJS`
   - **newapi 签到（浏览器模式）依赖**：`httpx playwright`
   - **完整依赖：**：`--upgrade pip && pip install requests PyExecJS httpx playwright && playwright install chromium`

3. **安装 Linux 依赖**

   进入青龙面板 → 依赖管理 → Linux：

   - **公共依赖**：无
   - **newapi 签到依赖**：`debianutils && apt-get update && apt-get install -y libgbm1 libglib2.0-0 libnss3 libnspr4 libxss1 libdrm2 libgtk-3-0 libasound2`

4. **配置环境变量**

   根据你要使用的服务，参考下方"📝 环境变量配置"章节添加对应的环境变量。

---

## 📝 环境变量配置

以下环境变量配置适用于 **GitHub Actions** 和 **青龙面板** 两种方式。

### 📢 通知配置（推荐）

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `TG_BOT_TOKEN` | Telegram 机器人 Token | 推荐 | `1234567890:AAG9rt...` |
| `TG_USER_ID` | Telegram 用户 ID | 推荐 | `1434078534` |
| `PUSH_KEY` | Server 酱推送 Key | 可选 | `SCT300842T...` |
| `QYWX_KEY` | 企业微信机器人 Key | 可选 | `5036ccf4-7f42...` |
| `PUSH_PLUS_TOKEN` | Push+ 推送 Token | 可选 | `xxxxxxxxxx` |
| `DD_BOT_TOKEN` | 钉钉机器人 Token | 可选 | `xxxxxxxxxx` |
| `DD_BOT_SECRET` | 钉钉机器人密钥 | 可选 | `xxxxxxxxxx` |
| `BARK_PUSH` | Bark 推送地址 | 可选 | `https://api.day.app/your_key/` |

**获取方式：**

**Telegram 配置获取：**
1. 创建机器人：与 [@BotFather](https://t.me/botfather) 对话，发送 `/newbot`
2. 获取 Token: 创建完成后会收到 `TG_BOT_TOKEN`
3. 获取用户 ID: 与 [@userinfobot](https://t.me/userinfobot) 对话获取 `TG_USER_ID`

**其他推送方式：**
- Server 酱：访问 [sct.ftqq.com](https://sct.ftqq.com) 获取
- 企业微信：企业微信群机器人
- Push+: 访问 [pushplus.plus](https://pushplus.plus) 获取
- Bark: iOS Bark 应用推送

</details>

### ☁️ 阿里云盘

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `ALIYUN_REFRESH_TOKEN` | refresh_token | 必需 | `crsh166bdfde4751a4c0...` |
| `AUTO_UPDATE_TOKEN` | 自动更新 Token | 可选 | `true` |
| `PRIVACY_MODE` | 隐私保护模式 | 可选 | `true` |

**获取方式：**
1. 浏览器访问 [阿里云盘网页版](https://www.aliyundrive.com/) 并登录
2. 按 `F12` 打开开发者工具 → `Application` 标签页
3. 左侧找到 `Local Storage` → `https://www.aliyundrive.com`
4. 找到 `token` 项，复制 `refresh_token` 的值
5. 多账号用 `&` 或换行分隔

**配置说明：**
- `AUTO_UPDATE_TOKEN`: 默认 `true`，自动维护 token（GitHub Actions 环境下会自动更新 Secrets）
- `PRIVACY_MODE`: 默认 `true`，脱敏显示敏感信息

</details>

### ☁️ 百度网盘

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `BAIDU_COOKIE` | 网站 Cookie | 必需 | `BDUSS=xxx; STOKEN=xxx...` |
| `PRIVACY_MODE` | 隐私模式 | 可选 | `true` |

**获取方式：**
1. 访问 [百度网盘](https://pan.baidu.com/) 并登录
2. 按 `F12` 打开开发者工具 → `Network` 标签页
3. 刷新页面，找到任意请求
4. 复制完整的 `Cookie` 值

</details>

### ☁️ 夸克网盘

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `QUARK_COOKIE` | 夸克网盘 Cookie | 必需 | `user=张三; kps=xxx; sign=yyy; vcode=zzz;` |

**获取方式：**
1. 使用**手机抓包工具**获取移动端 Cookie（推荐 [ProxyPin](https://github.com/wanghongenpin/network_proxy_flutter)）
2. 打开手机抓包工具，访问夸克网盘签到页
3. 找到接口 `https://drive-m.quark.cn/1/clouddrive/capacity/growth/info` 的请求信息
4. 复制请求中的参数：`kps`、`sign` 和 `vcode`
5. 按以下格式组合 Cookie：
   ```
   user=张三; kps=abcdefg; sign=hijklmn; vcode=111111111;
   ```
   - `user` 字段为用户名，可随意填写（用于日志区分）
   - `kps`、`sign`、`vcode` 为必需参数，从抓包中获取
6. 多账号配置：用 `&&` 或回车分隔

</details>

### ☁️ 天翼云盘

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `TY_USERNAME` | 登录手机号 | 必需 | `13812345678&13987654321` |
| `TY_PASSWORD` | 登录密码 | 必需 | `password1&password2` |

**获取方式：**
1. 浏览器访问 [天翼云盘](https://e.dlife.cn/index.do)，**关闭设备锁**
2. 使用手机号和密码登录
3. 多账号用 `&` 分隔，密码顺序需与手机号顺序对应

</details>

### 📱 NodeSeek

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `NODESEEK_COOKIE` | 网站 Cookie | 必需 | `cookie1&cookie2&cookie3` |
| `NS_RANDOM` | 签到随机参数 | 可选 | `true` |

**获取方式：**
1. 浏览器访问 [nodeseek.com](https://www.nodeseek.com) 并登录
2. 按 `F12` 打开开发者工具 → `Network` 标签页
3. 刷新页面，找到请求头中的 `Cookie`
4. 复制完整的 Cookie 值
5. 多账号用 `&` 分隔

</details>

### 🌊 DeepFlood

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `DEEPFLOOD_COOKIE` | 网站 Cookie | 必需 | `cookie1&cookie2` |
| `NS_RANDOM` | 签到随机参数 | 可选 | `true` |

**获取方式：**
1. 浏览器访问 [deepflood.com](https://www.deepflood.com) 并登录
2. 按 `F12` 打开开发者工具 → `Network` 标签页
3. 刷新页面，找到请求头中的 `Cookie`
4. 复制完整的 Cookie 值
5. 多账号用 `&` 分隔

</details>

### 🎮 NGA 论坛

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `NGA_CREDENTIALS` | UID,AccessToken | 必需 | `12345678,abcdef...` |

**获取方式：**
1. 安装抓包工具并开启 HTTPS 解密
   - Android：HTTP Canary、HttpToolkit、mitmproxy、Charles
   - iOS：Stream、Charles
2. 将手机的网络代理指向抓包工具（或使用工具的 VPN/代理模式）
3. 打开 NGA 官方 App，确保已登录，随便执行一个操作（进入首页/签到等）触发请求
4. 在抓包记录中找到对 `https://ngabbs.com/nuke.php` 的 POST 请求
5. 打开该请求的请求体，复制以下参数的值：
   - `access_uid`: 你的 UID
   - `access_token`: 一串长字符串
6. 按 `UID,AccessToken` 格式填写环境变量
   - 单账号示例：`123456,abcdefg`
   - 多账号用 `&` 分隔：`123456,abcdefg&234567,hijklmn`

</details>

### 📰 百度贴吧

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `TIEBA_COOKIE` | 百度贴吧 Cookie | 必需 | `BDUSS=xxxxxx; STOKEN=xxxxx...` |

**获取方式：**
1. 浏览器访问 [tieba.baidu.com](https://tieba.baidu.com) 并登录
2. 按 `F12` 打开开发者工具 → `Network` 标签页
3. 刷新页面，找到请求头中的完整 `Cookie`
4. 确保包含 `BDUSS` 参数
5. 多账号换行分隔

</details>

### 🛒 什么值得买

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `SMZDM_COOKIE` | 什么值得买 Cookie | 必需 | `__ckguid==xxxxx; device_id=xxxxx...` |

**获取方式：**
1. 浏览器访问 [什么值得买](https://www.smzdm.com/) 并登录
2. 按 `F12` 打开开发者工具 → `Network` 标签页
3. 刷新页面，找到任意请求的 `Request Headers`
4. 复制完整的 `Cookie` 值
5. 多账号换行分隔

</details>

### 📦 顺丰速运

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `SFSU_COOKIE` | 顺丰速运 URL | 必需 | `https://mcs-mimp...` |

**获取方式：**
1. 顺丰 APP 绑定微信后，添加机器人发送"顺丰"
2. 打开小程序或 APP → 我的 → 积分，抓包以下 URL 之一:
   - `https://mcs-mimp-web.sf-express.com/mcs-mimp/share/weChat/shareGiftReceiveRedirect`
   - `https://mcs-mimp-web.sf-express.com/mcs-mimp/share/app/shareRedirect`
3. 抓取 URL 后，使用 [URL 编码工具](https://www.toolhelper.cn/EncodeDecode/Url) 进行编码
4. 多账号换行分隔

</details>

### 🏔️ 恩山论坛

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `ENSHAN_COOKIE` | 恩山论坛 Cookie | 必需 | 完整的 Cookie 字符串 |

**获取方式：**
1. 浏览器访问 [恩山论坛](https://www.right.com.cn/FORUM/) 并登录
2. 按 `F12` 打开开发者工具 → `Network` 标签页
3. 刷新页面，找到请求头中的 `Cookie`
4. 复制完整的 Cookie 值

</details>

### 📓 有道云笔记

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `YOUDAO_COOKIE` | 有道云笔记 Cookie | 必需 | `__yadk_uid=xxx; YNOTE_SESS=xxx...` |

**获取方式：**
1. 浏览器访问 [有道云笔记](https://note.youdao.com/) 并登录
2. 按 `F12` 打开开发者工具 → `Network` 标签页
3. 刷新页面，找到任意请求
4. 查看请求的 Headers → Cookie：复制完整的 Cookie 值
5. 多账号换行分隔

**注意事项：**
- 必须包含 `YNOTE_PERS` 字段，脚本需要从中提取用户 ID
- Cookie 会定期过期，失效后需要重新获取

</details>

### 📡 iKuuu

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `IKUUU_EMAIL` | 登录邮箱 | 必需 | `user@example.com` |
| `IKUUU_PASSWD` | 登录密码 | 必需 | `password123` |
| `IKUUU_DOMAIN` | 自定义域名 | 可选 | `https://ikuuu.nl` |

**配置说明：**
- `IKUUU_DOMAIN`: 默认 `https://ikuuu.nl`，如果域名变更可在此修改
- 多账号用英文逗号分隔：`email1,email2`
- 密码顺序要与邮箱顺序对应：`password1,password2`

</details>

### 🏰 z.luxury

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `Z_LUXURY_EMAIL` | 登录账号 | 必需 | `413210209` |
| `Z_LUXURY_PASSWD` | 登录密码 | 必需 | `password123` |
| `YESCAPTCHA_CLIENT_KEY` | 打码平台 Key | 必需 | `43d97d5...` |
| `Z_LUXURY_DOMAIN` | 自定义域名 | 可选 | `https://z.luxury` |

**获取方式：**
1. **YesCaptcha Key**: 访问 [YesCaptcha](https://yescaptcha.com/) 注册并获取 Client Key (用于自动过 Recaptcha 验证码)
2. **账号密码**: 使用你的 z.luxury 登录账号和密码

**配置说明：**
- 多账号用英文逗号分隔：`email1,email2`
- 密码顺序要与邮箱顺序对应：`password1,password2`
- `YESCAPTCHA_CLIENT_KEY`: 必填，否则无法通过验证码

</details>

### 🌊 Leaflow

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `LEAFLOW_COOKIE` | Cookie（JSON 数组格式） | 必需 | 见下方说明 |

**获取方式：**
1. 浏览器访问 [leaflow](https://leaflow.net/workspaces) 并登录
2. 按 `F12` 打开开发者工具 → `Application` 标签页
3. 左侧找到 Cookies → `https://leaflow.net`
4. 复制以下三个 cookie 的完整值：
   - `leaflow_session`：会话 token（通常以 eyJ 开头）
   - `remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d`：持久化登录 token
   - `XSRF-TOKEN`：CSRF 防护 token
5. 将 cookie 字符串转换为 JSON 数组格式：

**配置示例：**
```json
[
  {
    "leaflow_session": "你的 session 值",
    "remember_web_xxx": "你的 remember 值",
    "XSRF-TOKEN": "你的 token 值"
  }
]
```

**多账号示例：**
```json
[
  {"leaflow_session": "xxx1", "remember_web_xxx": "yyy1", "XSRF-TOKEN": "zzz1"},
  {"leaflow_session": "xxx2", "remember_web_xxx": "yyy2", "XSRF-TOKEN": "zzz2"}
]
```

</details>

### 🌐 NewAPI 通用签到（GemAI / AnyRouter / AgentRouter / 996Coder 等）

<details>
<summary>点击展开配置</summary>

所有基于 NewAPI 二次开发的站点均使用同一个脚本 `newapi_checkin.py`，通过 `NEWAPI_ACCOUNTS` 统一配置。

| 变量名 | 说明 | 是否必需 |
|--------|------|----------|
| `NEWAPI_ACCOUNTS` | 账号配置（JSON 数组） | 必需 |
| `BROWSER_HEADLESS` | 浏览器无头模式（浏览器模式生效） | 可选，默认 `true` |
| `NEWAPI_TIMEOUT` | 请求超时秒数（Cookie 模式生效） | 可选，默认 `30` |
| `NEWAPI_VERIFY_SSL` | SSL 证书验证（Cookie 模式生效） | 可选，默认 `true` |
| `NEWAPI_MAX_RETRIES` | 最大重试次数（Cookie 模式生效） | 可选，默认 `3` |

**认证方式通过账号字段自动判断：**
- 含 `cookies` + `api_user` 字段 → **Cookie 模式**（轻量，使用 requests 直接调 API，适合 GemAI、AnyRouter、AgentRouter 等）
- 含 `email` + `password` 字段 → **浏览器模式**（Playwright 模拟登录，适合 996Coder 等）

**签到接口：**
- 默认调用 `POST /api/user/checkin`
- 若站点使用其他路径（如 AnyRouter 的 `/api/user/sign_in`），在账号中加 `checkin_path` 字段覆盖
- `checkin_path` 设为 `""` 表示登录即触发签到，不主动调用接口（此配置已废弃，所有站点统一使用 Cookie 模式）

---

**Cookie 模式账号示例（GemAI）：**
```json
[
  {
    "name": "GemAI 账号 1",
    "base_url": "https://api.gemai.cc",
    "cookies": "session=你的 session 值",
    "api_user": "你的 api_user 值"
  }
]
```

**Cookie 模式账号示例（AnyRouter，需覆盖签到路径）：**
```json
[
  {
    "name": "AnyRouter 账号 1",
    "base_url": "https://anyrouter.top",
    "checkin_path": "/api/user/sign_in",
    "cookies": "session=你的 session 值",
    "api_user": "你的 api_user 值"
  }
]
```

**Cookie 模式账号示例（AgentRouter）：**
```json
[
  {
    "name": "AgentRouter-zengql",
    "base_url": "https://agentrouter.org",
    "cookies": "session=MTc2MjI0MDQ1OHxEWDhFQVFM...",
    "api_user": "40548"
  }
]
```

**浏览器模式账号示例（996Coder）：**
```json
[
  {
    "name": "996Coder 账号 1",
    "base_url": "https://996coder.com",
    "email": "user@example.com",
    "password": "your_password"
  }
]
```

**混合多账号示例（不同站点写在同一个数组里）：**
```json
[
  {
    "name": "GemAI-zengqinglei",
    "base_url": "https://api.gemai.cc",
    "cookies": "cf_clearance=xxx; session=MTc3NjIzNTQ1NnxEWDhFQVFM...",
    "api_user": "137004"
  },
  {
    "name": "AnyRouter",
    "base_url": "https://anyrouter.top",
    "checkin_path": "/api/user/sign_in",
    "cookies": "session=yyy",
    "api_user": "67890"
  },
  {
    "name": "AgentRouter-zengql",
    "base_url": "https://agentrouter.org",
    "cookies": "session=MTc2MjI0MDQ1OHxEWDhFQVFM...",
    "api_user": "40548"
  },
  {
    "name": "996Coder",
    "base_url": "https://996coder.com",
    "email": "user@example.com",
    "password": "password123"
  }
]
```

**Cookie 获取方式（Cookie 模式）：**
1. 浏览器访问对应站点并登录
2. 按 `F12` 打开开发者工具 → `Network` 标签页
3. 刷新页面，找到任意 API 请求（如 `/api/user/self`）
4. 查看请求 Headers：
   - `Cookie`：复制完整值（包含 `cf_clearance` 和 `session`，用分号 + 空格分隔）
   - `new-api-user`：复制该请求头的值（即 `api_user`）

**Cookie 格式说明：**
- GemAI 等站点需要完整的 Cookie 字符串，格式：`cf_clearance=xxx; session=yyy`
- session 值通常很长（以 `MT` 开头的 base64 编码字符串），请确保完整复制

**⚠️ 注意事项：**
- 浏览器模式需要安装 Playwright：`pip install playwright && playwright install chromium`
- 密码存储在环境变量中，请确保环境安全
- 新站点若签到接口路径不同，通过 `checkin_path` 字段指定即可

</details>

---

### 🌐 代理配置（高级）

<details>
<summary>点击展开配置</summary>

GitHub Actions 环境默认会使用 WARP 代理以绕过 IP 限制。如果某些脚本（如 Leaflow）在使用代理时出现问题，可以通过配置 `NO_PROXY_SCRIPTS` 环境变量使其直连。

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `NO_PROXY_SCRIPTS` | 不走代理的脚本列表 | 可选 | `leaflow,ikuuu` |

**配置说明：**
- 值为脚本名称（不带后缀），多个脚本用逗号分隔
- 示例：`leaflow` 表示 leaflow_checkin.py 将不走代理直连
- 仅在 GitHub Actions 环境下生效

</details>

### 📄 免责声明

- 本项目仅供学习交流使用，请勿用于商业用途
- 使用本项目所产生的任何问题，作者不承担任何责任
- 请遵守相关网站的使用条款和法律法规

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源协议。
