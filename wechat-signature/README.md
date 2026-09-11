# 微信 JS-SDK 签名云函数部署指南（腾讯云 CloudBase）

## 1. 部署云函数

1. 登录 [腾讯云 CloudBase 控制台](https://console.cloud.tencent.com/tcb)（无环境先免费创建一个，选上海/广州地域）
2. 「云函数」→ 新建函数 → 名称 `wechat-signature` → 运行环境 Node.js16.13 → 上传本目录（index.js + package.json）
3. 「函数配置」→「环境变量」中添加：

   | 变量名 | 值 |
   |---|---|
   | `WECHAT_APP_ID` | 公众号 AppID（在公众号后台「设置与开发→基本配置」） |
   | `WECHAT_APP_SECRET` | 公众号 AppSecret（**只填在这里，绝不进前端/git**） |

   可选变量：
   - `ALLOWED_HOSTS`：允许签名的页面域名，逗号分隔（默认 `haust-reunion.surge.sh`；以后绑定自有域名时改成新域名）
   - `ALLOWED_ORIGIN`：CORS 放行来源（默认 `https://haust-reunion.surge.sh`）

4. 「云函数 → 函数详情 → 访问服务/HTTP 触发」开启 HTTP 访问（鉴权选"免鉴权"），得到形如
   `https://<环境ID>.<地域>.tcloudbaseapp.com/wechat-signature` 的地址
5. 把该地址填入网页项目 `wechat-share.js` 顶部的 `SIGNATURE_API`，重新部署 surge

## 2. 固定出口 IP（公众号 IP 白名单用）

微信公众号获取 access_token 要求调用方 IP 在「基本配置→IP白名单」内。

- SCF/CloudBase 默认出口 IP 不固定：在函数「网络配置」中开启 **固定公网出口 IP**（NAT 网关方式）
- 开启后控制台会显示实际出口 IP —— **以控制台显示为准**，把它加入公众号 IP 白名单
- 不要使用任何猜测的 IP

## 3. 公众号后台还需要的配置

1. 「设置与开发→公众号设置→功能设置→**JS接口安全域名**」：
   - 微信要求该域名**已通过 ICP 备案**。`haust-reunion.surge.sh` 属于 surge.sh 子域，无法备案，
     大概率**不能**通过此项设置 —— 这不是代码问题，是微信的平台规则
   - 正式做法：绑定一个你自己的**已备案域名**（CNAME 指向 surge，或把静态站迁到国内对象存储），
     然后把该域名填入 JS 安全域名，同时更新 `ALLOWED_HOSTS` / `ALLOWED_ORIGIN` / `WECHAT_SHARE.link`
2. 添加安全域名时微信会要求下载 `MP_verify_xxxx.txt` —— 把该文件发我（或自行放到
   surge 部署目录一起 `node deploy.js`），确保 `https://你的域名/MP_verify_xxxx.txt` 可直接访问
3. 分享接口 `updateAppMessageShareData` 需要**认证的**服务号/订阅号；个人未认证订阅号调用会失败

## 4. 缓存说明

- access_token / jsapi_ticket 缓存在函数实例内存，TTL 7000 秒（官方 7200 秒，提前刷新）
- CloudBase 多实例不共享缓存：冷启动新实例会多取一次 token。本站访问量极小，
  远低于微信每日 2000 次 access_token 上限；如需收紧可开启「单实例多并发」
