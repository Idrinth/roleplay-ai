(() => {
  let page = 1;
  const pages = [
    document.getElementById("worlds"),
    document.getElementById("chat"),
    document.getElementsByTagName("article")[0],
    document.getElementById("documents"),
    document.getElementById("characters")
  ].filter(e => !!e) as HTMLElement[];
  let initX = 0;
  const switchPage = () => {
    if (page < 0) {
      page = pages.length - 1;
    } else if (page > pages.length - 1) {
      page = 0;
    }
    document.getElementById('content')?.setAttribute('data-page', `${page}`);
  }
  document.addEventListener("keyup", (event: KeyboardEvent) => {
    if (event.key === "ArrowLeft") {
      page--;
    }
    if (event.key === "ArrowRight") {
      page++;
    }
    switchPage();
  })
  document.addEventListener("touchstart", (event: TouchEvent) => {
    initX = event.touches[0]?.pageX ?? 0;
  })
  document.addEventListener("touchend", (event: TouchEvent) => {
    const endX = event.touches[event.touches.length - 1]?.clientX ?? 0;
    if (endX - initX > 100) {
      page++;
    } else if (endX - initX < 100) {
      page--;
    }
    switchPage();
  })
})();
