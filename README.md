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

### 环境要求

- 青龙面板 2.10+
- Node.js 14+

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

**注意：**
- 必须使用**移动端抓包**，PC端Cookie无法使用
- Cookie有效期约为**12小时**，建议每天更新
- 必须包含 `kps`、`sign`、`vcode` 三个参数
- 失效后会返回401错误，需重新抓包获取

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
