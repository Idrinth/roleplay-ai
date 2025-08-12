(() => {
  let page = 1;
  const pages = [
    document.getElementById("worlds"),
    document.getElementById("chat"),
    document.getElementsByTagName("article")[0],
    document.getElementById("documents"),
    document.getElementById("characters")
  ].filter(e => !!e) as HTMLElement[];
  const switchPage = () => {
    if (page < 0) {
      page = pages.length - 1;
    } else if (page > pages.length - 1) {
      page = 0;
    }
    document.getElementById('content')?.setAttribute('data-page', `${page}`);
  }
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
