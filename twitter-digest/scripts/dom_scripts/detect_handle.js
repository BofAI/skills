(() => {
  const RESERVED_PATHS = new Set([
    'home', 'explore', 'notifications', 'messages', 'i', 'search', 'settings',
    'compose', 'jobs', 'premium', 'verified-orgs', 'privacy', 'tos',
    'login', 'signup', 'logout', 'download', 'intent', 'share', 'hashtag',
  ]);
  const validHandle = (value) => /^[A-Za-z0-9_]{1,15}$/.test(value || '') && !RESERVED_PATHS.has(String(value).toLowerCase());
  const cleanHandle = (value) => {
    const text = String(value || '');
    const match = text.match(/@([A-Za-z0-9_]{1,15})/);
    return match && validHandle(match[1]) ? match[1] : null;
  };
  const handleFromHref = (href) => {
    if (!href) return null;
    let parsed;
    try {
      parsed = new URL(href, location.href);
    } catch (_) {
      return null;
    }
    if (!/(^|\.)x\.com$|(^|\.)twitter\.com$/.test(parsed.hostname)) return null;
    const parts = parsed.pathname.split('/').filter(Boolean);
    if (parts.length !== 1) return null;
    return validHandle(parts[0]) ? parts[0] : null;
  };
  const fromText = (...values) => {
    for (const value of values) {
      const handle = cleanHandle(value);
      if (handle) return handle;
    }
    return null;
  };

  const account = document.querySelector('[data-testid="SideNav_AccountSwitcher_Button"]');
  const accountText = account ? account.innerText : '';
  const accountMatch = fromText(accountText, account && account.getAttribute('aria-label'));
  if (accountMatch) return accountMatch;

  const profileLink = document.querySelector('[data-testid="AppTabBar_Profile_Link"]');
  const profileHref = profileLink ? profileLink.getAttribute('href') : '';
  const profileHrefMatch = handleFromHref(profileHref);
  if (profileHrefMatch) return profileHrefMatch;
  const profileTextMatch = fromText(profileLink && profileLink.innerText, profileLink && profileLink.getAttribute('aria-label'));
  if (profileTextMatch) return profileTextMatch;

  const accountLikeNodes = Array.from(document.querySelectorAll([
    '[data-testid*="Account"]',
    '[data-testid*="account"]',
    '[aria-label*="account" i]',
    '[aria-label*="profile" i]',
    '[aria-label*="账号"]',
    '[aria-label*="帳號"]',
    '[aria-label*="账户"]',
    '[aria-label*="个人资料"]',
    '[aria-label*="個人資料"]',
  ].join(',')));
  for (const node of accountLikeNodes) {
    const handle = fromText(node.innerText, node.getAttribute('aria-label'), node.getAttribute('title'));
    if (handle) return handle;
    const linkHandle = handleFromHref(node.getAttribute('href') || '');
    if (linkHandle) return linkHandle;
  }

  const nav = document.querySelector('nav') || document.body;
  const navProfileLinks = Array.from(nav.querySelectorAll('a[href]')).filter((link) => {
    const text = `${link.innerText || ''} ${link.getAttribute('aria-label') || ''}`;
    return /profile|account|账号|帳號|账户|个人资料|個人資料/i.test(text);
  });
  for (const link of navProfileLinks) {
    const handle = handleFromHref(link.getAttribute('href') || '') || fromText(link.innerText, link.getAttribute('aria-label'));
    if (handle) return handle;
  }

  return null;
})()
