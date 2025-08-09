(() => {
  const footer = document.createElement("footer");
  const worlds = document.createElement("worlds");
  const documents = document.createElement("documents");
  const characters = document.createElement("characters");
  const content = document.getElementById("content");
  if (!content) {
    return;
  }
  const data = {footer, worlds, documents, characters};
  for (const element of Object.keys(data)) {
    if (Object.hasOwn(data, element)) {
      const item = data[element as 'documents'|'characters'|'worlds'|'footer'] as HTMLElement;
      for (const event of ['mouseenter', 'focusin']) {
        item.addEventListener(event, () => {
          content.classList.add(`hovers-${element}`);
        });
      }
      for (const event of ['mouseleave', 'focusout']) {
        item.addEventListener(event, () => {
          content.classList.remove(`hovers-${element}`);
        });
      }
    }
  }
})();
