(async() => {
  if (window.matchMedia && !window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.getElementsByTagName('html')[0]?.classList.toggle('inverted-colors');
  }
  if (window.localStorage) {
    const preferedColorScheme = window.localStorage.getItem('prefered-color-scheme');
    if (preferedColorScheme === 'dark') {
      document.getElementsByTagName('html')[0]?.classList.remove('inverted-colors');
    } else if (preferedColorScheme === 'light') {
      document.getElementsByTagName('html')[0]?.classList.add('inverted-colors');
    }
    window.localStorage.setItem('prefered-color-scheme', document.getElementsByTagName('html')[0]?.classList.contains('inverted-colors') ? 'light' : 'dark');
  }
  document.getElementById('logo').onclick = () => {
    document.getElementsByTagName('html')[0]?.classList.toggle('inverted-colors');
    window.localStorage && window.localStorage.setItem(
      'prefered-color-scheme',
      document.getElementsByTagName('html')[0]?.classList.contains('inverted-colors') ? 'light' : 'dark',
    );
  }
})();
