(() => {
  const panel = document.querySelector('[data-testid="dm-conversation-panel"]')
    || document.querySelector('[data-testid="dm-conversation-content"]')
    || document.querySelector('main')
    || document.body;
  const roots = messageRoots(panel);
  return roots.filter((node) => {
    const bubble = node.querySelector('[data-testid^="message-text-"]');
    const text = bubbleText(bubble || node);
    const rect = node.getBoundingClientRect();
    return Boolean(text) && rect.width > 20 && rect.height > 12;
  }).length;

  function bubbleText(node) {
    if (!node) return '';
    const parts = [];
    for (const child of Array.from(node.querySelectorAll('span, div[dir="auto"]'))) {
      const text = clean(child.innerText || '');
      if (!text || isTimeText(text)) continue;
      const style = getComputedStyle(child);
      if (style.opacity === '0' || style.visibility === 'hidden' || style.display === 'none') continue;
      parts.push(text);
    }
    return Array.from(new Set(parts)).join(' ').trim();
  }
  function clean(text) { return (text || '').replace(/\s+/g, ' ').trim(); }
  function isTimeText(text) { return /^(\d{1,2}:\d{2}\s?(AM|PM)?|\d{1,2}:\d{2}|上午\s*\d{1,2}:\d{2}|下午\s*\d{1,2}:\d{2})$/i.test(text); }
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
