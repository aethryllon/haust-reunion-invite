/* ============================================================
 * 微信分享 JSSDK 模块（wechat-share.js）
 * - 仅在微信内置浏览器中工作；其余环境直接退出
 * - 签名服务未部署 / 不可达 / 公众号未配置时自动降级为
 *   <head> 中的 meta(og:/itemprop:) 分享方案，页面不受任何影响
 * - 本文件不包含、也绝不请求任何公众号密钥
 * ============================================================ */
(function () {
  'use strict';

  /* ---------- 配置区 ---------- */
  // 签名服务地址：部署 wechat-signature 云函数后，把其 HTTP 访问地址填到这里。
  // 留空 = JSSDK 不启用，自动走 meta 降级方案（页面其余功能完全不受影响）。
  var SIGNATURE_API = '';   // 例：'https://xxxx.xxxxx.tcloudbaseapp.com/wechat-signature'

  var WECHAT_SHARE = {
    title: '科大廿载 · 青春再聚｜机制025班毕业20周年同学聚会邀请函',
    desc: '2026年10月2日—4日，相约洛阳 · 河南科技大学西苑校区。廿载光阴，再回西苑，共赴青春之约。',
    link: 'https://haust-reunion.surge.sh/',
    imgUrl: 'https://haust-reunion.surge.sh/share-logo-v2.jpg'
  };

  /* ---------- 调试支持（?wxdebug=1，仅输出到浏览器控制台，页面上不显示任何东西） ---------- */
  var debugMode = /[?&]wxdebug=1(?:&|$)/.test(location.search);
  function dbg(step, ok) {
    if (debugMode && window.console) {
      try { console.log('[wx-share]', step); } catch (e) {}
    }
  }

  /* ---------- 环境判断 ---------- */
  var isWechat = /MicroMessenger/i.test(navigator.userAgent);
  dbg('浏览器: ' + (isWechat ? '微信内置' : '非微信（普通浏览器）'));

  if (!isWechat) { dbg('非微信环境，跳过 JSSDK，使用 meta 方案'); return; }
  if (typeof wx === 'undefined') { dbg('jweixin-1.6.0.js 未加载成功，降级 meta 方案', false); return; }
  if (!SIGNATURE_API) { dbg('未配置 SIGNATURE_API（签名服务未部署），降级 meta 方案'); return; }

  /* ---------- 请求签名（XHR，兼容老内核） ---------- */
  var signUrl = location.href.split('#')[0];
  dbg('待签名 URL: ' + signUrl);

  function getConfig(fn) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', SIGNATURE_API + '?url=' + encodeURIComponent(signUrl), true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState !== 4) return;
      if (xhr.status !== 200) { fn('签名服务 HTTP ' + xhr.status); return; }
      try {
        var data = JSON.parse(xhr.responseText);
        if (data && data.signature && data.appId && data.timestamp && data.nonceStr) {
          fn(null, data);
        } else {
          fn('签名服务返回异常: ' + (data && data.error ? data.error : xhr.responseText.slice(0, 120)));
        }
      } catch (e) { fn('签名响应解析失败'); }
    };
    xhr.onerror = function () { fn('签名服务不可达'); };
    try { xhr.send(null); } catch (e) { fn(String(e)); }
  }

  getConfig(function (err, cfg) {
    if (err) { dbg(err + '，降级 meta 方案', false); return; }
    dbg('签名获取成功 appId=' + cfg.appId);

    wx.config({
      debug: false,
      appId: cfg.appId,
      timestamp: cfg.timestamp,
      nonceStr: cfg.nonceStr,
      signature: cfg.signature,
      jsApiList: ['updateAppMessageShareData', 'updateTimelineShareData']
    });

    wx.ready(function () {
      dbg('wx.ready 触发，注册分享内容');
      wx.updateAppMessageShareData({
        title: WECHAT_SHARE.title,
        desc: WECHAT_SHARE.desc,
        link: WECHAT_SHARE.link,
        imgUrl: WECHAT_SHARE.imgUrl,
        fail: function (res) { dbg('updateAppMessageShareData 失败: ' + JSON.stringify(res), false); }
      });
      wx.updateTimelineShareData({
        title: WECHAT_SHARE.title,
        link: WECHAT_SHARE.link,
        imgUrl: WECHAT_SHARE.imgUrl,
        fail: function (res) { dbg('updateTimelineShareData 失败: ' + JSON.stringify(res), false); }
      });
     
    });

    wx.error(function (res) {
      // 常见原因：公众号未配置 JS 安全域名 / 签名过期 / IP 白名单未加云函数出口 IP
      dbg('wx.error: ' + JSON.stringify(res), false);
     
    });
  });
})();
