(async() => {
  if (window.matchMedia && !window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.getElementsByTagName('html')[0]?.classList.add('inverted-colors');
    document.getElementById('peerlist')?.firstElementChild?.setAttribute('src', 'https://peerlist.io/api/v1/projects/embed/PRJHGNQ86JOPGEP7RF8E6QDP769BEN?showUpvote=true&theme=light');
  }
  if (window.localStorage) {
    const preferedColorScheme = window.localStorage.getItem('prefered-color-scheme');
    if (preferedColorScheme === 'dark') {
      document.getElementsByTagName('html')[0]?.classList.remove('inverted-colors');
    document.getElementById('peerlist')?.firstElementChild?.setAttribute('src', 'https://peerlist.io/api/v1/projects/embed/PRJHGNQ86JOPGEP7RF8E6QDP769BEN?showUpvote=true&theme=dark')
    } else if (preferedColorScheme === 'light') {
      document.getElementsByTagName('html')[0]?.classList.add('inverted-colors');
    document.getElementById('peerlist')?.firstElementChild?.setAttribute('src', 'https://peerlist.io/api/v1/projects/embed/PRJHGNQ86JOPGEP7RF8E6QDP769BEN?showUpvote=true&theme=light')
    }
    window.localStorage.setItem('prefered-color-scheme', document.getElementsByTagName('html')[0]?.classList.contains('inverted-colors') ? 'light' : 'dark');
  }
  document.getElementById('logo').onclick = () => {
    document.getElementsByTagName('html')[0]?.classList.toggle('inverted-colors');
    window.localStorage && window.localStorage.setItem(
      'prefered-color-scheme',
      document.getElementsByTagName('html')[0]?.classList.contains('inverted-colors') ? 'light' : 'dark',
    );

    document.getElementById('peerlist')?.firstElementChild?.setAttribute('src', 'https://peerlist.io/api/v1/projects/embed/PRJHGNQ86JOPGEP7RF8E6QDP769BEN?showUpvote=true&theme=' + (document.getElementsByTagName('html')[0]?.classList.contains('inverted-colors') ? 'light' : 'dark'));
  }
})();
