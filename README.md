# QL Script Hub

> 🚀 个人青龙面板脚本库 - 签到、薅羊毛一站式解决方案

[![GitHub stars](https://img.shields.io/github/stars/agluo/ql-script-hub?style=flat-square)](https://github.com/agluo/ql-script-hub/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/agluo/ql-script-hub?style=flat-square)](https://github.com/agluo/ql-script-hub/network)
[![GitHub issues](https://img.shields.io/github/issues/agluo/ql-script-hub?style=flat-square)](https://github.com/agluo/ql-script-hub/issues)
[![License](https://img.shields.io/github/license/agluo/ql-script-hub?style=flat-square)](https://github.com/agluo/ql-script-hub/blob/main/LICENSE)

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

1. **是否运行所有脚本**：
   - `true`（默认）：运行所有已配置的脚本
   - `false`：只运行下方选择的单个脚本

2. **选择要运行的单个脚本**（仅当第一项为 `false` 时生效）：
   - 从下拉列表中选择一个脚本（如 `ikuuu`、`aliyunpan`、`agentrouter` 等）

**说明：** 默认自动检测环境变量，只运行已配置的脚本。

### ⏰ 定时任务

**默认执行时间：** 每天北京时间 9:00 和 18:00（UTC 1:00 和 10:00）

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

- 仓库 60 天无提交，定时任务会被禁用
- AgentRouter 无头模式成功率较低
- 定时任务可能有 5-10 分钟延迟

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
   - **anyrouter 签到依赖**：`PyExecJS`
   - **agentrouter 签到依赖**：`httpx playwright`
   - **完整依赖：**：`--upgrade pip && pip install requests PyExecJS httpx playwright && playwright install chromium`

3. **安装 Linux 依赖**

   进入青龙面板 → 依赖管理 → Linux：

   - **公共依赖**：无
   - **agentrouter 签到依赖**：`debianutils && apt-get update && apt-get install -y libgbm1 libglib2.0-0 libnss3 libnspr4 libxss1 libdrm2 libgtk-3-0 libasound2`

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
| `TG_BOT_TOKEN` | Telegram机器人Token | 推荐 | `1234567890:AAG9rt...` |
| `TG_USER_ID` | Telegram用户ID | 推荐 | `1434078534` |
| `PUSH_KEY` | Server酱推送Key | 可选 | `SCT300842T...` |
| `QYWX_KEY` | 企业微信机器人Key | 可选 | `5036ccf4-7f42...` |
| `PUSH_PLUS_TOKEN` | Push+推送Token | 可选 | `xxxxxxxxxx` |
| `DD_BOT_TOKEN` | 钉钉机器人Token | 可选 | `xxxxxxxxxx` |
| `DD_BOT_SECRET` | 钉钉机器人密钥 | 可选 | `xxxxxxxxxx` |
| `BARK_PUSH` | Bark推送地址 | 可选 | `https://api.day.app/your_key/` |

**获取方式：**

**Telegram 配置获取：**
1. 创建机器人: 与 [@BotFather](https://t.me/botfather) 对话，发送 `/newbot`
2. 获取Token: 创建完成后会收到 `TG_BOT_TOKEN`
3. 获取用户ID: 与 [@userinfobot](https://t.me/userinfobot) 对话获取 `TG_USER_ID`

**其他推送方式：**
- Server酱: 访问 [sct.ftqq.com](https://sct.ftqq.com) 获取
- 企业微信: 企业微信群机器人
- Push+: 访问 [pushplus.plus](https://pushplus.plus) 获取
- Bark: iOS Bark 应用推送

</details>

### ☁️ 阿里云盘

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `ALIYUN_REFRESH_TOKEN` | refresh_token | 必需 | `crsh166bdfde4751a4c0...` |
| `AUTO_UPDATE_TOKEN` | 自动更新Token | 可选 | `true` |
| `PRIVACY_MODE` | 隐私保护模式 | 可选 | `true` |

**获取方式：**
1. 浏览器访问 [阿里云盘网页版](https://www.aliyundrive.com/) 并登录
2. 按 `F12` 打开开发者工具 → `Application` 标签页
3. 左侧找到 `Local Storage` → `https://www.aliyundrive.com`
4. 找到 `token` 项，复制 `refresh_token` 的值
5. 多账号用 `&` 或换行分隔

**配置说明：**
- `AUTO_UPDATE_TOKEN`: 默认 `true`，自动维护token
- `PRIVACY_MODE`: 默认 `true`，脱敏显示敏感信息

</details>

### ☁️ 百度网盘

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `BAIDU_COOKIE` | 网站Cookie | 必需 | `BDUSS=xxx; STOKEN=xxx...` |
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
| `QUARK_COOKIE` | 夸克网盘Cookie | 必需 | `user=张三; kps=xxx; sign=yyy; vcode=zzz;` |

**获取方式：**
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
| `NODESEEK_COOKIE` | 网站Cookie | 必需 | `cookie1&cookie2&cookie3` |
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
| `DEEPFLOOD_COOKIE` | 网站Cookie | 必需 | `cookie1&cookie2` |
| `NS_RANDOM` | 签到随机参数 | 可选 | `true` |

**获取方式：**
1. 浏览器访问 [deepflood.com](https://www.deepflood.com) 并登录
2. 按 `F12` 打开开发者工具 → `Network` 标签页
3. 刷新页面，找到请求头中的 `Cookie`
4. 复制完整的 Cookie 值
5. 多账号用 `&` 分隔

</details>

### 🎮 NGA论坛

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
   - `access_uid`: 你的UID
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
| `TIEBA_COOKIE` | 百度贴吧Cookie | 必需 | `BDUSS=xxxxxx; STOKEN=xxxxx...` |

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
| `SMZDM_COOKIE` | 什么值得买Cookie | 必需 | `__ckguid==xxxxx; device_id=xxxxx...` |

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
| `SFSU_COOKIE` | 顺丰速运URL | 必需 | `https://mcs-mimp...` |

**获取方式：**
1. 顺丰APP绑定微信后，添加机器人发送"顺丰"
2. 打开小程序或APP → 我的 → 积分，抓包以下URL之一:
   - `https://mcs-mimp-web.sf-express.com/mcs-mimp/share/weChat/shareGiftReceiveRedirect`
   - `https://mcs-mimp-web.sf-express.com/mcs-mimp/share/app/shareRedirect`
3. 抓取URL后，使用 [URL编码工具](https://www.toolhelper.cn/EncodeDecode/Url) 进行编码
4. 多账号换行分隔

</details>

### 🏔️ 恩山论坛

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `ENSHAN_COOKIE` | 恩山论坛Cookie | 必需 | 完整的Cookie字符串 |

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
| `YOUDAO_COOKIE` | 有道云笔记Cookie | 必需 | `__yadk_uid=xxx; YNOTE_SESS=xxx...` |

**获取方式：**
1. 浏览器访问 [有道云笔记](https://note.youdao.com/) 并登录
2. 按 `F12` 打开开发者工具 → `Network` 标签页
3. 刷新页面，找到任意请求
4. 查看请求的 Headers → Cookie：复制完整的 Cookie 值
5. 多账号换行分隔

**注意事项：**
- 必须包含 `YNOTE_PERS` 字段，脚本需要从中提取用户ID
- Cookie会定期过期，失效后需要重新获取

</details>

### 📡 iKuuu

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `IKUUU_EMAIL` | 登录邮箱 | 必需 | `user@example.com` |
| `IKUUU_PASSWD` | 登录密码 | 必需 | `password123` |

**配置说明：**
- 多账号用英文逗号分隔: `email1,email2`
- 密码顺序要与邮箱顺序对应: `password1,password2`

</details>

### 🌊 Leaflow

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `LEAFLOW_COOKIE` | Cookie（JSON数组格式） | 必需 | 见下方说明 |

**获取方式：**
1. 浏览器访问 [leaflow](https://leaflow.net/workspaces) 并登录
2. 按 `F12` 打开开发者工具 → `Application` 标签页
3. 左侧找到 Cookies → `https://leaflow.net`
4. 复制以下三个 cookie 的完整值：
   - `leaflow_session`：会话token（通常以 eyJ 开头）
   - `remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d`：持久化登录token
   - `XSRF-TOKEN`：CSRF防护token
5. 将 cookie 字符串转换为 JSON 数组格式：

**配置示例：**
```json
[
  {
    "leaflow_session": "你的session值",
    "remember_web_xxx": "你的remember值",
    "XSRF-TOKEN": "你的token值"
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

### 🌐 AnyRouter

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `ANYROUTER_ACCOUNTS` | 账号配置（JSON数组） | 必需 | 见下方说明 |
| `ANYROUTER_BASE_URL` | API基础地址 | 可选 | `https://anyrouter.top` |
| `ANYROUTER_TIMEOUT` | 请求超时时间（秒） | 可选 | `30` |
| `ANYROUTER_VERIFY_SSL` | SSL证书验证 | 可选 | `true` |
| `ANYROUTER_MAX_RETRIES` | 最大重试次数 | 可选 | `3` |

**获取方式：**
1. 浏览器访问 [AnyRouter](https://anyrouter.top) 并登录
2. 按 `F12` 打开开发者工具 → `Network` 标签页
3. 刷新页面，找到任意 API 请求（如 `/api/user/self`）
4. 查看请求的 Headers：
   - **Cookies**：复制 Cookie 字段的值（如 `session=xxx; token=xxx`）
   - **new-api-user**：复制该请求头的值（这是你的 api_user ID）
5. 将信息组合成 JSON 数组格式

**配置示例：**
```json
[
  {
    "cookies": {
      "session": "你的session值",
      "token": "你的token值"
    },
    "api_user": "你的api_user值"
  }
]
```

**注意事项：**
- 必须使用 JSON 数组格式 `[{}]`
- JSON 格式必须使用双引号
- 多账号添加多个对象，用逗号分隔
- 脚本会自动处理 WAF 挑战

</details>

### 🤖 AgentRouter

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `AGENTROUTER_ACCOUNTS` | Linux.do账号配置（JSON数组） | 必需 | 见下方说明 |
| `BROWSER_HEADLESS` | 浏览器无头模式 | 可选 | `true` |

**⚠️ 与 AnyRouter 的重要区别：**
- AgentRouter 使用 **Linux.do OAuth 认证**，不需要抓包获取 cookies
- 只需要提供 Linux.do 的登录账号和密码即可
- 脚本会自动使用 Playwright 浏览器完成 OAuth 认证流程

**配置步骤：**

1. **准备 Linux.do 账号**
   - 访问 [Linux.do](https://linux.do) 注册账号（如果还没有）
   - 记录你的登录邮箱和密码

2. **配置环境变量**

**单账号示例：**
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

**⚠️ 注意事项：**
- **青龙面板用户**: 必须安装 Playwright 和 Chromium 浏览器
  - 最小配置：CPU 100m + 内存 384MB（可运行但成功率较低）
  - 推荐配置：CPU 500m + 内存 1GB（成功率更高）
  - 建议设置 `BROWSER_HEADLESS=false` 使用有头模式，成功率更高
- **GitHub Actions 用户**: 只能使用无头模式，成功率较低（约 30-50%）
- 认证过程需要 30-60 秒，请耐心等待
- 如果认证失败，可以多次重试
- **安全提示**：密码会存储在环境变量中，请确保环境安全

</details>

### ⏰ 随机化配置（全局）

<details>
<summary>点击展开配置</summary>

| 变量名 | 说明 | 是否必需 | 示例值 |
|--------|------|----------|--------|
| `RANDOM_SIGNIN` | 启用随机签到 | 可选 | `true` |
| `MAX_RANDOM_DELAY` | 随机延迟窗口（秒） | 可选 | `3600` |

**配置说明：**
- `RANDOM_SIGNIN`: `true` 启用，`false` 禁用
- `MAX_RANDOM_DELAY`: `3600` = 1小时，`1800` = 30分钟
- 此配置对所有签到脚本生效

</details>

---

## 📄 免责声明

- 本项目仅供学习交流使用，请勿用于商业用途
- 使用本项目所产生的任何问题，作者不承担任何责任
- 请遵守相关网站的使用条款和法律法规

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源协议。

