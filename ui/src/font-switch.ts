(async() => {
  const setMode = (fontMode: 'default'|'custom') => {
    if (!fontMode) {
      fontMode = 'custom';
    }
    if (fontMode === 'custom') {
      document.getElementsByTagName('html')[0]?.classList.add('custom-fonts');
    } else {
      document.getElementsByTagName('html')[0]?.classList.remove('custom-fonts');
    }
    window?.localStorage?.setItem('preferred-font-mode', fontMode);
    return fontMode;
  }
  let prefersCustom = true;
  if (window.localStorage) {
    prefersCustom = setMode(window.localStorage.getItem('preferred-font-mode') as 'custom'|'default' ?? (prefersCustom ? 'custom' : 'default')) === 'custom';
  } else if(prefersCustom) {
    setMode('custom');
  }
  document.getElementById('fontmode')?.addEventListener('click', () => {
    prefersCustom = !prefersCustom;
    setMode(prefersCustom ? 'custom' : 'default');
  })
})();
