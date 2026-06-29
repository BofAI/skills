(() => {
  const account = document.querySelector('[data-testid="SideNav_AccountSwitcher_Button"]');
  const accountText = account ? account.innerText : '';
  const accountMatch = accountText.match(/@([A-Za-z0-9_]{1,15})/);
  if (accountMatch) return accountMatch[1];
  const profileLink = document.querySelector('[data-testid="AppTabBar_Profile_Link"]');
  const profileHref = profileLink ? profileLink.getAttribute('href') : '';
  const profileMatch = profileHref.match(/^\/([A-Za-z0-9_]{1,15})$/);
  if (profileMatch) return profileMatch[1];
  const labels = Array.from(document.querySelectorAll('[aria-label]')).map(el => el.getAttribute('aria-label') || '');
  for (const label of labels) {
    const match = label.match(/@([A-Za-z0-9_]{1,15})/);
    if (match && /account|profile|账号|帳號|账户/i.test(label)) return match[1];
  }
  return null;
})()
