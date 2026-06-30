(() => {
  const main = document.querySelector('main') || document.body;
  return (main.innerText || '').trim().slice(0, 12000);
})()
