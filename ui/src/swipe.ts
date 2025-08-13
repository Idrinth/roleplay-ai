(() => {
  let page = 1;
  const pages = [
    document.getElementById("worlds"),
    document.getElementById("chat"),
    document.getElementsByTagName("article")[0],
    document.getElementById("documents"),
    document.getElementById("characters")
  ].filter(e => !!e) as HTMLElement[];
  const dots = document.getElementById('swipe-dots');
  const switchPage = () => {
    if (page < 0) {
      page = pages.length - 1;
    } else if (page > pages.length - 1) {
      page = 0;
    }
    for (let i = 0; i < pages.length; i++) {
      dots?.children[i]?.classList.remove('active');
    }
    dots?.children[page]?.classList.add('active');
    document.getElementById('content')?.setAttribute('data-page', `${page}`);
  }
  for (let i = 0; i < pages.length; i++) {
    const li = document.createElement('li');
    li.appendChild(document.createElement('span'));
    li.onclick = () => {
      page = i;
      switchPage();
    }
    li.addEventListener('keydown', (ev: KeyboardEvent) => {
      if (ev.key === 'Enter' || ev.key === ' ') {
        ev.preventDefault();
        page = i;
        switchPage();
      }
    });
    li.setAttribute('role', 'button');
    li.setAttribute('tabindex', '0');
    li.setAttribute('aria-label', 'switch to page ' + (i + 1));
    dots?.appendChild(li);
  }
  dots?.children[page]?.classList.add('active');
  const mainnav = document.getElementById('mainnav');
  mainnav?.addEventListener('click', () => {
    mainnav.classList.toggle('active');
  });
  document.addEventListener("keyup", (event: KeyboardEvent) => {
    const target = event.target as HTMLElement | null;
    if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable)) {
      return;
    }
    if (event.key === "ArrowLeft") {
      page--;
    }
    if (event.key === "ArrowRight") {
      page++;
    }
    switchPage();
  });
  let initX: number|null = null;
  document.addEventListener("touchstart", (event: TouchEvent) => {
    initX = event.touches[0]?.pageX ?? null;
  });
  document.addEventListener("touchend", (event: TouchEvent) => {
    const endX = event.changedTouches[0]?.clientX ?? null;
    if (endX === null || initX === null) {
      return;
    }
    if (endX - initX > 100) {
      page++;
    } else if (endX - initX < -100) {
      page--;
    }
    switchPage();
  });
  document.getElementById('content')?.setAttribute('data-page', `${page}`);
})();
