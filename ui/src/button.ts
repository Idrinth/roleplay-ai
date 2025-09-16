((root) => {
  root.button = (text: string, title: string, callback: (ev: MouseEvent) => void, useActualButton: boolean = false): HTMLButtonElement|HTMLSpanElement => {
    const button = document.createElement(useActualButton ? 'button' : 'span');
    if (text === '[E]') {
      button.classList.add('edit');
    } else if (text === '[D]') {
      button.classList.add('delete');
    } else if (text === '[W]') {
      button.classList.add('wizard');
    }
    button.appendChild(document.createTextNode(text));
    button.setAttribute('title', title);
    if (! useActualButton) {
      button.classList.add('button');
      button.setAttribute('role', "button");
      button.setAttribute('aria-label', title);
    }
    button.onclick = callback;
    return button;
  }
})(window.bjoernbuettner)
