(() => {
  const panel = document.querySelector('[data-testid="dm-conversation-panel"]')
    || document.querySelector('[data-testid="dm-conversation-content"]')
    || document.querySelector('main')
    || document.body;
  const scroller = findScroller(panel);
  const roots = messageRoots(panel);
  const first = roots[0];
  return {
    count: roots.length,
    at_top: scroller ? scroller.scrollTop <= 2 : window.scrollY <= 0,
    scroll_top: scroller ? scroller.scrollTop : window.scrollY,
    top_signature: first ? signature(first) : '',
  };

  function findScroller(root) {
    const candidates = [root, ...Array.from(root.querySelectorAll('*'))].filter((el) => {
      const rect = el.getBoundingClientRect();
      return rect.width > 200 && rect.height > 200 && el.scrollHeight > el.clientHeight + 40;
    });
    return candidates.sort((a, b) => (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight))[0] || null;
  }
  function signature(node) {
    const text = (node.innerText || '').replace(/\s+/g, ' ').trim();
    const testid = node.getAttribute('data-testid') || '';
    const rect = node.getBoundingClientRect();
    return `${testid}:${Math.round(rect.top)}:${text.slice(0, 160)}`;
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
      const text = (node.innerText || '').replace(/\s+/g, ' ').trim();
      const rect = node.getBoundingClientRect();
      return text.length > 0 && text.length < 4000 && rect.width > 40 && rect.height > 16;
    });
  }
})()
