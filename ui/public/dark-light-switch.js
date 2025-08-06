(async() => {
  const setMode = (colorMode) => {
    if (!colorMode) {
      colorMode = 'dark';
    }
    if (colorMode === 'dark') {
      document.getElementsByTagName('html')[0]?.classList.remove('inverted-colors');
    } else {
      document.getElementsByTagName('html')[0]?.classList.add('inverted-colors');
    }
    document.getElementById('peerlist')?.firstElementChild?.setAttribute(
      'src',
      'https://peerlist.io/api/v1/projects/embed/PRJHGNQ86JOPGEP7RF8E6QDP769BEN?showUpvote=true&theme=' + colorMode
    );
    window?.localStorage?.setItem('preferred-color-scheme', colorMode);
    return colorMode;
  }
  let prefersLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
  if (window.localStorage) {
    prefersLight = setMode(window.localStorage.getItem('preferred-color-scheme') ?? (prefersLight ? 'light' : 'dark')) === 'light';
  } else if(prefersLight) {
    setMode('light');
  }
  document.getElementById('logo').onclick = () => {
    prefersLight = !prefersLight;
    setMode(prefersLight ? 'light' : 'dark');
  }
})();
