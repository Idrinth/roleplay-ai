window.bjoernbuettner = window.bjoernbuettner ||{};
((attachTo) => {
  const createModal = (text, label=false) => {
    const prmt = document.createElement('div');
    prmt.setAttribute('id', 'prompt');
    prmt.appendChild(document.createElement(label ? 'label' : 'p'));
    prmt.firstElementChild.appendChild(document.createTextNode(text));
    return prmt;
  }
  attachTo.prompt = async (text, defaultText = '') => {
    return new Promise(resolve => {
      const prmt = createModal(text, true);
      prmt.appendChild(document.createElement('input'));
      prmt.lastElementChild.value = defaultText;
      prmt.appendChild(bjoernbuettner.button('Send', 'Send changes', () => {
        if (!prmt.lastElementChild.previousElementSibling.value) {
          return;
        }
        document.body.removeChild(prmt);
        resolve(prmt.lastElementChild.previousElementSibling.value);
      }, true));
      document.body.appendChild(prmt);
    });
  }
  attachTo.confirm = async (text) => {
    return new Promise(resolve => {
      const prmt = createModal(text);
      prmt.appendChild(bjoernbuettner.button('Yes', 'Confirm', () => {
        document.body.removeChild(prmt);
        resolve(true);
      }, true));
      prmt.appendChild(bjoernbuettner.button('No', 'Deny', () => {
        document.body.removeChild(prmt);
        resolve(true);
      }, true));
      document.body.appendChild(prmt);
    });
  }
  attachTo.alert = async (text) => {
    return new Promise(resolve => {
      const prmt = createModal(text);
      prmt.appendChild(bjoernbuettner.button('OK', 'Confirm message', () => {
        document.body.removeChild(prmt);
        resolve();
      }, true));
      document.body.appendChild(prmt);
    });
  }
})(window.bjoernbuettner);
