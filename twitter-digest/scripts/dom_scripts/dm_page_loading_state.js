(() => {
  const main = document.querySelector('main') || document.body;
  const text = clean(main.innerText || '');
  const normalized = text.toLowerCase();
  const targets = document.querySelectorAll('a[href^="/messages/"], a[href^="/i/chat/"], a[href*="x.com/messages/"], a[href*="x.com/i/chat/"]').length;
  const skeletons = skeletonBlocks(main);
  const hasChatShell = /\bchat\b|\bmessages\b|聊天|私信/.test(normalized);
  const hasStartConversation = /start conversation|choose from your existing conversations|new chat/.test(normalized);
  const explicitEmpty = /welcome to your inbox|no messages/.test(normalized);
  return {
    text: text.slice(0, 1000),
    has_chat_shell: hasChatShell,
    has_start_conversation: hasStartConversation,
    explicit_empty: explicitEmpty,
    thread_target_count: targets,
    skeleton_count: skeletons.length,
    loading: hasChatShell && targets === 0 && !explicitEmpty && (skeletons.length >= 3 || hasStartConversation),
  };

  function skeletonBlocks(root) {
    const out = [];
    for (const el of Array.from(root.querySelectorAll('div, span'))) {
      const rect = el.getBoundingClientRect();
      if (rect.width < 35 || rect.height < 8 || rect.width > 420 || rect.height > 120) continue;
      if (rect.left < 70 || rect.left > Math.min(620, window.innerWidth * 0.55)) continue;
      const text = clean(el.innerText || '');
      if (text.length > 0) continue;
      const style = getComputedStyle(el);
      if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') continue;
      const bg = style.backgroundColor || '';
      const radius = parseFloat(style.borderRadius || '0') || 0;
      const lightBlock = /rgb\((23[0-9]|24[0-9]|25[0-5]),\s*(23[0-9]|24[0-9]|25[0-5]),\s*(23[0-9]|24[0-9]|25[0-5])\)/.test(bg)
        || /rgba\((23[0-9]|24[0-9]|25[0-5]),\s*(23[0-9]|24[0-9]|25[0-5]),\s*(23[0-9]|24[0-9]|25[0-5]),/.test(bg);
      if (!lightBlock && radius < 6) continue;
      out.push({
        x: Math.round(rect.left),
        y: Math.round(rect.top),
        width: Math.round(rect.width),
        height: Math.round(rect.height),
      });
    }
    return out;
  }
  function clean(value) { return (value || '').replace(/\s+/g, ' ').trim(); }
})()
