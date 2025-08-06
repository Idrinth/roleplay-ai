((root) => {
  const createModal = (text, label=false) => {
    const prmt = document.createElement('div');
    prmt.setAttribute('id', 'prompt');
    prmt.appendChild(document.createElement(label ? 'label' : 'p'));
    prmt.firstElementChild.appendChild(document.createTextNode(text));
    return prmt;
  }
  root.prompt = async (text, defaultText = '') => {
    return new Promise(resolve => {
      const prmt = createModal(text, true);
      prmt.appendChild(document.createElement('input'));
      prmt.lastElementChild.value = defaultText;
      prmt.appendChild(root.button('Send', 'Send changes', () => {
        if (!prmt.lastElementChild.previousElementSibling.value) {
          return;
        }
        document.body.removeChild(prmt);
        resolve(prmt.lastElementChild.previousElementSibling.value);
      }, true));
      document.body.appendChild(prmt);
    });
  }
  root.confirm = async (text) => {
    return new Promise(resolve => {
      const prmt = createModal(text);
      prmt.appendChild(root.button('Yes', 'Confirm', () => {
        document.body.removeChild(prmt);
        resolve(true);
      }, true));
      prmt.appendChild(root.button('No', 'Deny', () => {
        document.body.removeChild(prmt);
        resolve(false);
      }, true));
      document.body.appendChild(prmt);
    });
  }
  root.alert = async (text) => {
    return new Promise(resolve => {
      const prmt = createModal(text);
      prmt.appendChild(root.button('OK', 'Confirm message', () => {
        document.body.removeChild(prmt);
        resolve();
      }, true));
      document.body.appendChild(prmt);
    });
  }
})(window.bjoernbuettner);
