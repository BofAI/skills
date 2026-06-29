(() => {
  const panel = document.querySelector('[data-testid="dm-conversation-panel"]') || document.querySelector('[data-testid="conversationPanel"]') || document.querySelector('main') || document.body;
  return (panel.innerText || '').trim().slice(0, 12000);
})()
