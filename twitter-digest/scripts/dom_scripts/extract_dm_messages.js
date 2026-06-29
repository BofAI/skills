(() => {
  const panel = document.querySelector('[data-testid="dm-conversation-panel"]')
    || document.querySelector('[data-testid="dm-conversation-content"]')
    || document.querySelector('main')
    || document.body;
  const roots = messageRoots(panel);
  const out = [];
  const seen = new Set();
  for (const node of roots) {
    const bubble = node.querySelector('[data-testid^="message-text-"]');
    const text = bubbleText(bubble || node);
    if (!text) continue;
    const rect = node.getBoundingClientRect();
    if (rect.width < 20 || rect.height < 12) continue;
    const key = `${Math.round(rect.top)}:${text.slice(0, 120)}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const time = firstTimeText(bubble || node);
    const classText = String(node.className || '');
    const assets = messageAssets(node);
    out.push({
      sender: classText.includes('justify-end') ? 'me' : 'other',
      time,
      text,
      links: assets.links,
      media: assets.media,
    });
  }
  return out.slice(-Math.max(1, %d));

  function bubbleText(node) {
    if (!node) return '';
    const leafParts = [];
    for (const child of Array.from(node.querySelectorAll('span'))) {
      const text = clean(child.innerText || '');
      if (!text || isTimeText(text)) continue;
      const style = getComputedStyle(child);
      if (style.opacity === '0' || style.visibility === 'hidden' || style.display === 'none') continue;
      leafParts.push(text);
    }
    if (leafParts.length) return Array.from(new Set(leafParts)).join(' ').trim();
    const text = clean(node.innerText || '');
    return stripTrailingTimes(text);
  }
  function firstTimeText(node) {
    if (!node) return '';
    for (const child of Array.from(node.querySelectorAll('span, div'))) {
      const text = clean(child.innerText || '');
      if (isTimeText(text)) return text;
    }
    const match = clean(node.innerText || '').match(/(\d{1,2}:\d{2}\s?(?:AM|PM)?|上午\s*\d{1,2}:\d{2}|下午\s*\d{1,2}:\d{2})/i);
    return match ? match[1] : '';
  }
  function stripTrailingTimes(text) {
    let value = clean(text);
    for (let i = 0; i < 3; i += 1) {
      value = value.replace(/\s+(\d{1,2}:\d{2}\s?(?:AM|PM)?|上午\s*\d{1,2}:\d{2}|下午\s*\d{1,2}:\d{2})$/i, '').trim();
    }
    return value;
  }
  function clean(text) { return (text || '').replace(/\s+/g, ' ').trim(); }
  function isTimeText(text) { return /^(\d{1,2}:\d{2}\s?(AM|PM)?|\d{1,2}:\d{2}|上午\s*\d{1,2}:\d{2}|下午\s*\d{1,2}:\d{2})$/i.test(text); }
  function messageAssets(node) {
    const links = [];
    for (const a of Array.from(node.querySelectorAll('a[href]'))) {
      const href = normalizeUrl(a.getAttribute('href'));
      if (!href) continue;
      const label = clean(a.innerText || a.getAttribute('aria-label') || '');
      if (!links.some((item) => item.url === href)) links.push({url: href, label});
    }
    const media = [];
    for (const img of Array.from(node.querySelectorAll('img[src]'))) {
      const src = normalizeUrl(img.getAttribute('src'));
      if (!src) continue;
      const alt = clean(img.getAttribute('alt') || img.getAttribute('aria-label') || '');
      if (!media.some((item) => item.url === src)) media.push({type: 'image', url: src, alt});
    }
    for (const video of Array.from(node.querySelectorAll('video'))) {
      const src = normalizeUrl(video.currentSrc || video.getAttribute('src'));
      const poster = normalizeUrl(video.getAttribute('poster'));
      if (src || poster) media.push({type: 'video', url: src || '', poster: poster || '', alt: clean(video.getAttribute('aria-label') || '')});
    }
    return {links: links.slice(0, 10), media: media.slice(0, 8)};
  }
  function normalizeUrl(value) {
    if (!value || value.startsWith('data:') || value.startsWith('blob:')) return '';
    try {
      const url = new URL(value, location.href);
      url.hash = '';
      return url.href;
    } catch {
      return '';
    }
  }
  function messageRoots(root) {
    const byMessage = Array.from(root.querySelectorAll('div[data-testid^="message-"]'))
      .filter((node) => !String(node.getAttribute('data-testid') || '').startsWith('message-text-'));
    if (byMessage.length) return byMessage;
    const byText = Array.from(root.querySelectorAll('[data-testid^="message-text-"]'))
      .map((node) => node.closest('li, [role="group"]') || node.parentElement)
      .filter(Boolean);
    if (byText.length) return Array.from(new Set(byText));
    return Array.from(root.querySelectorAll('li, [role="group"]')).filter((node) => {
      const text = clean(node.innerText || '');
      const rect = node.getBoundingClientRect();
      return text.length > 0 && text.length < 4000 && rect.width > 40 && rect.height > 16;
    });
  }
})()
