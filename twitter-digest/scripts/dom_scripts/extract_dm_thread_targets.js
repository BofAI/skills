(() => {
  const seen = new Set();
  const ignoredText = /^(messages|new message|message requests|search direct messages|search|settings|home|profile|notifications)$/i;
  const ignoredShortText = /^(all|chat)$/i;
  const visible = (el) => {
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    return rect.width > 40 && rect.height > 24 && style.visibility !== 'hidden' && style.display !== 'none';
  };
  const clean = (text) => (text || '').replace(/\s+/g, ' ').trim();
  const out = [];

  const replyMeta = (el, label) => {
    const text = clean(label).toLowerCase();
    const aria = clean(el.getAttribute('aria-label') || '').toLowerCase();
    const combined = `${text} ${aria}`;
    const reasons = [];
    if (/\byou\s*[:：]|\byou sent\b|\byou replied\b|\byou responded\b|你\s*[:：]|你已发送|你发送|您\s*[:：]/i.test(combined)) {
      reasons.push('self_reply_label');
    }
    return { replied: reasons.length > 0, reply_reason: reasons.join(',') };
  };
  const timeMeta = (el) => {
    const parts = [];
    for (const node of Array.from(el.querySelectorAll('time'))) {
      parts.push(clean(node.getAttribute('datetime') || ''));
      parts.push(clean(node.getAttribute('title') || ''));
      parts.push(clean(node.getAttribute('aria-label') || ''));
      parts.push(clean(node.innerText || ''));
    }
    parts.push(clean(el.getAttribute('title') || ''));
    parts.push(clean(el.getAttribute('aria-label') || ''));
    return parts.filter(Boolean).join(' ');
  };

  for (const a of document.querySelectorAll('a[href^="/messages/"], a[href^="/i/chat/"], a[href*="x.com/messages/"], a[href*="x.com/i/chat/"]')) {
    if (!visible(a)) continue;
    const url = new URL(a.getAttribute('href'), location.href);
    url.search = '';
    url.hash = '';
    const label = clean(a.innerText || a.getAttribute('aria-label') || '');
    if (!/^https:\/\/(x|twitter)\.com\/(messages\/[^/]+|i\/chat\/[^/]+)/.test(url.href)) continue;
    if (/\/messages\/compose$/.test(url.pathname)) continue;
    if (!label || ignoredText.test(label) || ignoredShortText.test(label)) continue;
    const key = url.href;
    if (seen.has(key)) continue;
    seen.add(key);
    const meta = replyMeta(a, label);
    const rect = a.getBoundingClientRect();
    out.push({
      target_type: 'link',
      url: url.href,
      label,
      time_hint: timeMeta(a),
      x: rect.left + Math.min(rect.width / 2, 280),
      y: rect.top + rect.height / 2,
      ...meta
    });
  }

  const hasThreadMarker = (label) => (
    /\byou\s*[:：]|\byou sent\b|\byou replied\b|\byou responded\b|你\s*[:：]|你已发送|你发送|您\s*[:：]/i.test(label)
    || /\b(now|just now|\d+\s*(m|min|mins|minute|minutes|h|hr|hrs|hour|hours))\b/i.test(label)
    || /(刚刚|\d+\s*(秒|分钟|小时)|今天|今日|上午|下午|晚上|中午)/.test(label)
  );

  const candidates = Array.from(document.querySelectorAll([
    '[role="button"]',
    '[role="link"]',
    '[data-testid*="conversation" i]',
    '[data-testid*="cell" i]',
    '[data-testid="cellInnerDiv"]',
    'a[href*="/messages/"]',
    'div[aria-label]',
    'section div',
    'aside div'
  ].join(',')));
  for (const node of candidates) {
    if (!visible(node)) continue;
    let label = clean(node.innerText || node.getAttribute('aria-label') || '');
    if (!label || label.length < 2 || ignoredText.test(label) || ignoredShortText.test(label)) continue;
    if (label.length > 600) continue;
    if (!/[A-Za-z0-9_\u4e00-\u9fff]/.test(label)) continue;
    let rect = node.getBoundingClientRect();
    const link = node.querySelector && node.querySelector('a[href*="/messages/"], a[href*="/i/chat/"]');
    if (link) {
      const linkLabel = clean(link.innerText || link.getAttribute('aria-label') || '');
      const linkRect = link.getBoundingClientRect();
      if (linkLabel && hasThreadMarker(linkLabel) && linkRect.width > 40 && linkRect.height > 24) {
        label = linkLabel;
        rect = linkRect;
      }
    }
    if (!link && rect.left < 150) continue;
    if (!link && rect.height > 220) continue;
    const isLikelyListRow = rect.left < Math.min(760, window.innerWidth * 0.45) && rect.width > 160 && rect.height >= 36 && rect.height < 180;
    if (!link && !hasThreadMarker(label)) continue;
    if (!node.matches('[role="button"], [role="link"], [data-testid*="conversation" i], [data-testid*="cell" i], [data-testid="cellInnerDiv"], a[href*="/messages/"], div[aria-label]') && (!isLikelyListRow || !hasThreadMarker(label))) continue;
    let url = '';
    if (link) {
      const parsed = new URL(link.getAttribute('href'), location.href);
      parsed.search = '';
      parsed.hash = '';
      url = parsed.href;
    }
    const key = url || `${Math.round(rect.left)}:${Math.round(rect.top)}:${label.slice(0, 80)}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const meta = replyMeta(node, label);
    out.push({
      target_type: url ? 'row_link' : 'row_click',
      url,
      label,
      time_hint: timeMeta(node),
      x: rect.left + Math.min(rect.width / 2, 280),
      y: rect.top + rect.height / 2,
      ...meta
    });
  }
  return out.slice(0, 20);
})()
