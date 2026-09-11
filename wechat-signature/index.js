/**
 * 微信 JS-SDK 签名服务（腾讯云 CloudBase 云函数）
 * ============================================================
 * 接口：GET /wechat-signature?url=<前端当前页面URL>
 * 返回：{ appId, timestamp, nonceStr, signature }
 *
 * 安全设计：
 *  - AppSecret 只从云函数环境变量读取（WECHAT_APP_ID / WECHAT_APP_SECRET），
 *    绝不出现在前端、git、或任何返回体中
 *  - 只为白名单域名（默认 haust-reunion.surge.sh）签名，防接口被第三方滥用
 *  - CORS 仅放行 https://haust-reunion.surge.sh
 *
 * 缓存策略：
 *  - access_token 与 jsapi_ticket 均缓存在云函数实例内存中，TTL 7000 秒
 *    （微信官方有效期 7200 秒，提前 200 秒刷新）
 *  - CloudBase 多实例时缓存不共享：最坏情况每个新实例各取一次 token。
 *    本场景（班级邀请函，日访问量极小）远低于微信 access_token
 *    每日 2000 次获取上限；如需严格单实例，可在函数配置中开启
 *    「单实例多并发」以复用热实例。
 *
 * 签名算法（严格按微信官方规则，勿改字段名与顺序——按字典序）：
 *   sha1( 'jsapi_ticket=TICKET&noncestr=NONCE&timestamp=TS&url=URL' )
 *   注意：签名字符串中是全小写 noncestr，返回字段是驼峰 nonceStr
 */
'use strict';

const https = require('https');
const crypto = require('crypto');

/* 允许签名的页面域名（逗号分隔，可按需增删；支持以后绑定自定义域名） */
const ALLOWED_HOSTS = (process.env.ALLOWED_HOSTS || 'haust-reunion.surge.sh')
  .split(',').map(function (s) { return s.trim().toLowerCase(); }).filter(Boolean);
const ALLOWED_ORIGIN = process.env.ALLOWED_ORIGIN || 'https://haust-reunion.surge.sh';

const TOKEN_TTL = 7000; /* 秒 */
let cache = { accessToken: null, ticket: null, tokenExpireAt: 0, ticketExpireAt: 0 };

/* ---------- 工具：HTTPS GET，返回解析后的 JSON ---------- */
function getJSON(host, path) {
  return new Promise(function (resolve, reject) {
    const req = https.get({ host: host, path: path, timeout: 8000 }, function (res) {
      let buf = '';
      res.on('data', function (c) { buf += c; });
      res.on('end', function () {
        try { resolve(JSON.parse(buf)); } catch (e) { reject(new Error('微信接口响应解析失败')); }
      });
    });
    req.on('timeout', function () { req.destroy(new Error('微信接口请求超时')); });
    req.on('error', reject);
  });
}

/* ---------- access_token（带缓存） ---------- */
async function getAccessToken(appId, secret) {
  const now = Date.now();
  if (cache.accessToken && now < cache.tokenExpireAt) return cache.accessToken;
  const data = await getJSON('api.weixin.qq.com',
    '/cgi-bin/token?grant_type=client_credential&appid=' + encodeURIComponent(appId) +
    '&secret=' + encodeURIComponent(secret));
  if (!data.access_token) {
    throw new Error('获取 access_token 失败: errcode=' + data.errcode + ' ' + data.errmsg +
      '（请检查：AppID/AppSecret 是否正确；公众号后台「IP白名单」是否已加入本云函数出口IP）');
  }
  cache.accessToken = data.access_token;
  cache.tokenExpireAt = now + TOKEN_TTL * 1000;
  return cache.accessToken;
}

/* ---------- jsapi_ticket（带缓存） ---------- */
async function getJsapiTicket(appId, secret) {
  const now = Date.now();
  if (cache.ticket && now < cache.ticketExpireAt) return cache.ticket;
  const token = await getAccessToken(appId, secret);
  const data = await getJSON('api.weixin.qq.com',
    '/cgi-bin/ticket/getticket?access_token=' + encodeURIComponent(token) + '&type=jsapi');
  if (!data.ticket) {
    throw new Error('获取 jsapi_ticket 失败: errcode=' + data.errcode + ' ' + data.errmsg);
  }
  cache.ticket = data.ticket;
  cache.ticketExpireAt = now + TOKEN_TTL * 1000;
  return cache.ticket;
}

/* ---------- 云函数入口（HTTP 访问触发） ---------- */
exports.main = async function (event) {
  const q = (event.queryStringParameters || {});
  const origin = (event.headers && (event.headers.origin || event.headers.Origin)) || '';
  const corsHead = {
    'Access-Control-Allow-Origin': (origin === ALLOWED_ORIGIN) ? origin : ALLOWED_ORIGIN,
    'Access-Control-Allow-Methods': 'GET,OPTIONS',
    'Content-Type': 'application/json; charset=utf-8'
  };

  function reply(statusCode, body) {
    return { statusCode: statusCode, headers: corsHead, body: JSON.stringify(body) };
  }

  /* CORS 预检 */
  if (event.httpMethod === 'OPTIONS' || event.method === 'OPTIONS') {
    return { statusCode: 204, headers: corsHead, body: '' };
  }

  try {
    const appId = process.env.WECHAT_APP_ID;
    const secret = process.env.WECHAT_APP_SECRET;
    if (!appId || !secret) {
      return reply(500, { error: '尚未配置环境变量 WECHAT_APP_ID / WECHAT_APP_SECRET（请在云函数配置中填写）' });
    }

    /* 只为白名单域名的页面签名，防滥用 */
    const pageUrl = q.url || '';
    let host = '';
    try { host = new URL(pageUrl).hostname.toLowerCase(); } catch (e) { host = ''; }
    if (!host || ALLOWED_HOSTS.indexOf(host) === -1) {
      return reply(403, { error: '拒绝为该域名签名: ' + (host || '(空)') });
    }

    const ticket = await getJsapiTicket(appId, secret);
    const nonceStr = crypto.randomBytes(8).toString('hex');
    const timestamp = Math.floor(Date.now() / 1000);

    /* 微信官方签名串：字段按字典序，noncestr 全小写 */
    const raw = 'jsapi_ticket=' + ticket +
                '&noncestr=' + nonceStr +
                '&timestamp=' + timestamp +
                '&url=' + pageUrl;
    const signature = crypto.createHash('sha1').update(raw, 'utf8').digest('hex');

    return reply(200, {
      appId: appId,
      timestamp: timestamp,
      nonceStr: nonceStr,
      signature: signature
    });
  } catch (err) {
    return reply(502, { error: String(err && err.message || err) });
  }
};
