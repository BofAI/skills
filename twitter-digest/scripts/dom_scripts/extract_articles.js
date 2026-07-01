(() => {
  const statusUrl = (href) => {
    try {
      const url = new URL(href, location.href);
      return /\/status\/\d+/.test(url.pathname) ? url.href : null;
    } catch { return null; }
  };
  const clean = (text) => (text || '').replace(/\s+/g, ' ').trim();
  const normalizeUrl = (value) => {
    if (!value || value.startsWith('data:') || value.startsWith('blob:')) return '';
    try {
      const url = new URL(value, location.href);
      url.hash = '';
      return url.href;
    } catch { return ''; }
  };
  const linkInfo = (article, links) => {
    const out = [];
    for (const a of Array.from(article.querySelectorAll('a[href]'))) {
      const url = normalizeUrl(a.getAttribute('href'));
      if (!url) continue;
      let parsed;
      try { parsed = new URL(url); } catch { continue; }
      if (/\/photo\/\d+/.test(parsed.pathname)) continue;
      if (/\/analytics$|\/retweets$|\/likes$/.test(parsed.pathname)) continue;
      const label = clean(a.innerText || a.getAttribute('aria-label') || '');
      const isStatus = /\/status\/\d+/.test(parsed.pathname);
      const sameStatus = isStatus && links.map(statusUrl).includes(url);
      const isProfile = /^\/[^/]+$/.test(parsed.pathname) && (parsed.hostname.endsWith('x.com') || parsed.hostname.endsWith('twitter.com'));
      if (sameStatus || isProfile) continue;
      if (!out.some((item) => item.url === url)) out.push({url, label});
    }
    return out.slice(0, 12);
  };
  const mediaInfo = (article) => {
    const out = [];
    for (const img of Array.from(article.querySelectorAll('img[src]'))) {
      const url = normalizeUrl(img.getAttribute('src'));
      if (!url) continue;
      if (/profile_images|emoji|hashflags|abs\.twimg\.com\/responsive-web/i.test(url)) continue;
      const alt = clean(img.getAttribute('alt') || img.getAttribute('aria-label') || '');
      if (!out.some((item) => item.url === url)) out.push({type: 'image', url, alt});
    }
    for (const video of Array.from(article.querySelectorAll('video'))) {
      const url = normalizeUrl(video.currentSrc || video.getAttribute('src'));
      const poster = normalizeUrl(video.getAttribute('poster'));
      if (url || poster) out.push({type: 'video', url, poster, alt: clean(video.getAttribute('aria-label') || '')});
    }
    return out.slice(0, 8);
  };
  const cardInfo = (article) => {
    const cards = [];
    for (const link of Array.from(article.querySelectorAll('a[href]'))) {
      const text = clean(link.innerText || link.getAttribute('aria-label') || '');
      const href = normalizeUrl(link.getAttribute('href'));
      if (!href || text.length < 8) continue;
      try {
        const parsed = new URL(href);
        const isProfile = /^\/[^/]+$/.test(parsed.pathname) && (parsed.hostname.endsWith('x.com') || parsed.hostname.endsWith('twitter.com'));
        if (isProfile) continue;
        if (/\/status\/\d+/.test(parsed.pathname) && text.length < 80) continue;
      } catch { continue; }
      if (!cards.some((item) => item.url === href && item.text === text)) cards.push({url: href, text: text.slice(0, 500)});
    }
    return cards.slice(0, 5);
  };
  return Array.from(document.querySelectorAll('article')).map((article) => {
    const text = (article.innerText || '').trim();
    const links = Array.from(article.querySelectorAll('a[href]')).map(a => a.href).filter(Boolean);
    const status = links.map(statusUrl).find(Boolean) || null;
    let tweetId = null;
    if (status) {
      try {
        const match = new URL(status).pathname.match(/\/status\/(\d+)/);
        tweetId = match ? match[1] : null;
      } catch {}
    }
    const times = Array.from(article.querySelectorAll('time')).map(t => t.getAttribute('datetime')).filter(Boolean);
    const authorLinks = links.filter(h => {
      try {
        const p = new URL(h).pathname;
        return /^\/[^/]+$/.test(p) && !p.includes('/i/');
      } catch { return false; }
    });
    let authorUsername = null;
    if (authorLinks[0]) {
      try {
        authorUsername = new URL(authorLinks[0]).pathname.split('/').filter(Boolean)[0] || null;
      } catch {}
    }
    return {
      id: tweetId,
      text,
      url: status,
      links,
      externalLinks: linkInfo(article, links),
      media: mediaInfo(article),
      cards: cardInfo(article),
      time: times[0] || null,
      authorUrl: authorLinks[0] || null,
      authorUsername
    };
  }).filter(item => item.text);
})()
