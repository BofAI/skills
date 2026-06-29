(() => {
  const scroller = findThreadListScroller();
  if (!scroller) {
    const before = window.scrollY;
    window.scrollBy(0, Math.max(700, window.innerHeight * 0.8));
    return {found: false, before, after: window.scrollY, at_bottom: window.innerHeight + window.scrollY >= document.body.scrollHeight - 4};
  }
  const before = scroller.scrollTop;
  const step = Math.max(500, scroller.clientHeight * 0.85);
  scroller.scrollTop = Math.min(scroller.scrollHeight - scroller.clientHeight, before + step);
  scroller.dispatchEvent(new Event('scroll', {bubbles: true}));
  return {
    found: true,
    before,
    after: scroller.scrollTop,
    at_bottom: scroller.scrollTop + scroller.clientHeight >= scroller.scrollHeight - 4,
    scroll_height: scroller.scrollHeight,
    client_height: scroller.clientHeight,
  };

  function findThreadListScroller() {
    const candidates = Array.from(document.querySelectorAll('main, aside, section, div')).filter((el) => {
      const rect = el.getBoundingClientRect();
      if (rect.width < 220 || rect.height < 220) return false;
      if (rect.left > Math.min(820, window.innerWidth * 0.55)) return false;
      if (el.scrollHeight <= el.clientHeight + 40) return false;
      const text = clean(el.innerText || '');
      const hasThreadLink = !!el.querySelector('a[href^="/messages/"], a[href^="/i/chat/"], a[href*="x.com/messages/"], a[href*="x.com/i/chat/"]');
      const looksLikeInbox = /\b(chat|messages|search)\b/i.test(text) || /(聊天|私信|搜索)/.test(text);
      return hasThreadLink || looksLikeInbox;
    });
    return candidates.sort((a, b) => {
      const ar = a.getBoundingClientRect();
      const br = b.getBoundingClientRect();
      const aScore = (a.scrollHeight - a.clientHeight) - ar.left;
      const bScore = (b.scrollHeight - b.clientHeight) - br.left;
      return bScore - aScore;
    })[0] || null;
  }
  function clean(text) { return (text || '').replace(/\s+/g, ' ').trim(); }
})()
