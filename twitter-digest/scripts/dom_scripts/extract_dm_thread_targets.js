(() => {
  const MIN_VISIBLE_WIDTH_PX = 40;
  const MIN_VISIBLE_HEIGHT_PX = 24;
  const CLICK_X_MAX_OFFSET_PX = 280;
  const MAX_LABEL_LENGTH = 600;
  const DEDUPE_LABEL_PREFIX_LENGTH = 80;
  const LEFT_NAV_CUTOFF_PX = 150;
  const MAX_NON_LINK_ROW_HEIGHT_PX = 220;
  const LIST_COLUMN_MAX_WIDTH_PX = 760;
  const LIST_COLUMN_WIDTH_RATIO = 0.45;
  const MIN_LIST_ROW_WIDTH_PX = 160;
  const MIN_LIST_ROW_HEIGHT_PX = 36;
  const MAX_LIST_ROW_HEIGHT_PX = 180;
  const MAX_THREAD_TARGETS = 20;
  const SUPPORTED_ROW_SELECTOR = [
    '[role="button"]',
    '[role="link"]',
    '[data-testid*="conversation" i]',
    '[data-testid*="cell" i]',
    '[data-testid="cellInnerDiv"]',
    'a[href*="/messages/"]',
    'div[aria-label]'
  ].join(',');
  const SELF_REPLY_RE = /\byou\s*[:：]|\byou sent\b|\byou replied\b|\byou responded\b|你\s*[:：]|你已发送|你发送|您\s*[:：]/i;
  const RECENT_TIME_RE = /\b(now|just now|\d+\s*(m|min|mins|minute|minutes|h|hr|hrs|hour|hours))\b/i;
  const RECENT_TIME_CN_RE = /(刚刚|\d+\s*(秒|分钟|小时)|今天|今日|上午|下午|晚上|中午)/;
  const seen = new Set();
  const ignoredText = /^(messages|new message|message requests|search direct messages|search|settings|home|profile|notifications)$/i;
  const ignoredShortText = /^(all|chat)$/i;
  const visible = (el) => {
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    return rect.width > MIN_VISIBLE_WIDTH_PX && rect.height > MIN_VISIBLE_HEIGHT_PX && style.visibility !== 'hidden' && style.display !== 'none';
  };
  const clean = (text) => (text || '').replace(/\s+/g, ' ').trim();
  const clickX = (rect) => rect.left + Math.min(rect.width / 2, CLICK_X_MAX_OFFSET_PX);
  const out = [];

  const replyMeta = (el, label) => {
    const text = clean(label).toLowerCase();
    const aria = clean(el.getAttribute('aria-label') || '').toLowerCase();
    const combined = `${text} ${aria}`;
    const reasons = [];
    if (SELF_REPLY_RE.test(combined)) {
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
      x: clickX(rect),
      y: rect.top + rect.height / 2,
      ...meta
    });
  }

  const hasThreadMarker = (label) => (
    SELF_REPLY_RE.test(label)
    || RECENT_TIME_RE.test(label)
    || RECENT_TIME_CN_RE.test(label)
  );
  const isSupportedInteractiveNode = (node) => node.matches(SUPPORTED_ROW_SELECTOR);
  const looksLikeThreadListRow = (rect, label) => (
    rect.left < Math.min(LIST_COLUMN_MAX_WIDTH_PX, window.innerWidth * LIST_COLUMN_WIDTH_RATIO)
    && rect.width > MIN_LIST_ROW_WIDTH_PX
    && rect.height >= MIN_LIST_ROW_HEIGHT_PX
    && rect.height < MAX_LIST_ROW_HEIGHT_PX
    && hasThreadMarker(label)
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
    if (label.length > MAX_LABEL_LENGTH) continue;
    if (!/[A-Za-z0-9_\u4e00-\u9fff]/.test(label)) continue;
    let rect = node.getBoundingClientRect();
    const link = node.querySelector && node.querySelector('a[href*="/messages/"], a[href*="/i/chat/"]');
    if (link) {
      const linkLabel = clean(link.innerText || link.getAttribute('aria-label') || '');
      const linkRect = link.getBoundingClientRect();
      if (linkLabel && hasThreadMarker(linkLabel) && linkRect.width > MIN_VISIBLE_WIDTH_PX && linkRect.height > MIN_VISIBLE_HEIGHT_PX) {
        label = linkLabel;
        rect = linkRect;
      }
    }
    if (!link && rect.left < LEFT_NAV_CUTOFF_PX) continue;
    if (!link && rect.height > MAX_NON_LINK_ROW_HEIGHT_PX) continue;
    const isLikelyListRow = looksLikeThreadListRow(rect, label);
    if (!link && !hasThreadMarker(label)) continue;
    if (!isSupportedInteractiveNode(node) && !isLikelyListRow) continue;
    let url = '';
    if (link) {
      const parsed = new URL(link.getAttribute('href'), location.href);
      parsed.search = '';
      parsed.hash = '';
      url = parsed.href;
    }
    const key = url || `${Math.round(rect.left)}:${Math.round(rect.top)}:${label.slice(0, DEDUPE_LABEL_PREFIX_LENGTH)}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const meta = replyMeta(node, label);
    out.push({
      target_type: url ? 'row_link' : 'row_click',
      url,
      label,
      time_hint: timeMeta(node),
      x: clickX(rect),
      y: rect.top + rect.height / 2,
      ...meta
    });
  }
  return out.slice(0, MAX_THREAD_TARGETS);
})()
