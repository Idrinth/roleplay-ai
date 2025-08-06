window.bjoernbuettner = window.bjoernbuettner || {};
((addTo) => {
  addTo.button = (text, title, callback, useActualButton = false) => {
    const button = document.createElement(useActualButton ? 'button' : 'span');
    button.appendChild(document.createTextNode(text));
    button.setAttribute('title', title);
    if (!useActualButton) {
      button.classList.add('button');
      button.setAttribute('role', "button");
      button.setAttribute('aria-label', title);
    }
    button.onclick = callback;
    return button;
  }
})(window.bjoernbuettner)
