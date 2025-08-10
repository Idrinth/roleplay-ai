(() => {
  const footer = document.getElementById('footer');
  const worlds = document.getElementById('worlds');
  const documents = document.getElementById('documents');
  const characters = document.getElementById('characters');
  const content = document.getElementById('content');
  if (!content) {
    return;
  }
  const elements = {footer, worlds, documents, characters};
  for (const element of Object.keys(elements)) {
    if (Object.hasOwn(elements, element)) {
      const item = elements[element as keyof typeof elements] as HTMLElement|null;
      for (const event of ['mouseenter', 'focusin']) {
        item?.addEventListener(event, () => {
          content.classList.add(`hovers-${element}`);
        });
      }
      for (const event of ['mouseleave', 'focusout']) {
        item?.addEventListener(event, () => {
          content.classList.remove(`hovers-${element}`);
        });
      }
    }
  }
})();
