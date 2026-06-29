(() => {
  const windowHours = Math.max(1, %d);
  const oldest = oldestLoadedMessageAgeHours();
  return Number.isFinite(oldest) && oldest > windowHours;

  function oldestLoadedMessageAgeHours() {
    const panel = document.querySelector('[data-testid="dm-conversation-panel"]')
      || document.querySelector('[data-testid="dm-conversation-content"]')
      || document.querySelector('main')
      || document.body;
    const list = panel.querySelector('[data-testid="dm-message-list"]') || panel;
    const items = Array.from(list.querySelectorAll('li'));
    let currentDay = '';
    let oldest = -Infinity;
    for (const item of items) {
      const text = clean(item.innerText || '');
      if (!text) continue;
      const roots = messageRoots(item);
      if (!roots.length) {
        const day = dayLabel(text);
        if (day) currentDay = day;
        continue;
      }
      for (const root of roots) {
        const timeText = firstTimeText(root);
        const when = parseMessageDate(currentDay, timeText);
        if (!when) continue;
        const age = (Date.now() - when.getTime()) / 36e5;
        if (age > oldest) oldest = age;
      }
    }
    return oldest;
  }
  function dayLabel(text) {
    const value = clean(text);
    if (/^(today|yesterday|今天|昨天)$/i.test(value)) return value;
    if (/^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2}/i.test(value)) return value;
    if (/^\d{4}[\/-]\d{1,2}[\/-]\d{1,2}$/.test(value)) return value;
    if (/^\d{1,2}[\/-]\d{1,2}(?:[\/-]\d{2,4})?$/.test(value)) return value;
    return '';
  }
  function parseMessageDate(day, timeText) {
    const time = parseTime(timeText);
    if (!time) return null;
    const base = parseDay(day);
    if (!base) return null;
    base.setHours(time.hours, time.minutes, 0, 0);
    return base;
  }
  function parseDay(day) {
    const now = new Date();
    const value = clean(day).toLowerCase();
    if (!value || value === 'today' || value === '今天') return new Date(now.getFullYear(), now.getMonth(), now.getDate());
    if (value === 'yesterday' || value === '昨天') return new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
    const parsed = new Date(day);
    if (!Number.isNaN(parsed.getTime())) return new Date(parsed.getFullYear(), parsed.getMonth(), parsed.getDate());
    return null;
  }
  function firstTimeText(node) {
    for (const child of Array.from(node.querySelectorAll('span, div'))) {
      const text = clean(child.innerText || '');
      if (isTimeText(text)) return text;
    }
    const match = clean(node.innerText || '').match(/(\d{1,2}:\d{2}\s?(?:AM|PM)?|上午\s*\d{1,2}:\d{2}|下午\s*\d{1,2}:\d{2})/i);
    return match ? match[1] : '';
  }
  function parseTime(text) {
    const value = clean(text);
    let match = value.match(/^(\d{1,2}):(\d{2})\s?(AM|PM)$/i);
    if (match) {
      let hours = Number(match[1]);
      const minutes = Number(match[2]);
      const suffix = match[3].toUpperCase();
      if (suffix === 'PM' && hours < 12) hours += 12;
      if (suffix === 'AM' && hours === 12) hours = 0;
      return {hours, minutes};
    }
    match = value.match(/^(上午|下午)\s*(\d{1,2}):(\d{2})$/);
    if (match) {
      let hours = Number(match[2]);
      const minutes = Number(match[3]);
      if (match[1] === '下午' && hours < 12) hours += 12;
      if (match[1] === '上午' && hours === 12) hours = 0;
      return {hours, minutes};
    }
    match = value.match(/^(\d{1,2}):(\d{2})$/);
    if (match) return {hours: Number(match[1]), minutes: Number(match[2])};
    return null;
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
    if (root.matches && root.matches('li, [role="group"]')) {
      const text = clean(root.innerText || '');
      const rect = root.getBoundingClientRect();
      if (text.length > 0 && text.length < 4000 && rect.width > 40 && rect.height > 16) return [root];
    }
    return [];
  }
})()
