(() => {
  const panel = document.querySelector('[data-testid="dm-conversation-panel"]')
    || document.querySelector('[data-testid="dm-conversation-content"]')
    || document.querySelector('main')
    || document.body;
  const candidates = [panel, ...Array.from(panel.querySelectorAll('*'))].filter((el) => {
    const rect = el.getBoundingClientRect();
    return rect.width > 200 && rect.height > 200 && el.scrollHeight > el.clientHeight + 40;
  });
  const scroller = candidates.sort((a, b) => (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight))[0];
  if (!scroller) {
    window.scrollBy(0, -Math.max(900, window.innerHeight * 0.9));
    return {found: false, at_top: window.scrollY <= 0, scroll_top: window.scrollY};
  }
  const before = scroller.scrollTop;
  scroller.scrollTop = Math.max(0, before - Math.max(900, scroller.clientHeight * 0.9));
  scroller.dispatchEvent(new Event('scroll', {bubbles: true}));
  return {found: true, at_top: scroller.scrollTop <= 0, scroll_top: scroller.scrollTop, before};
})()
