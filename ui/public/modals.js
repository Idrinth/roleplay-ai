window.bjoernbuettner = window.bjoernbuettner ||{};
((attachTo) => {
  attachTo.prompt = async (text, defaultText = '') => {
    return new Promise(resolve => {
      const prmt = document.createElement('div');
      prmt.setAttribute('id', 'prompt');
      prmt.appendChild(document.createElement('label'));
      prmt.firstElementChild.appendChild(document.createTextNode(text));
      prmt.appendChild(document.createElement('input'));
      prmt.lastElementChild.value = defaultText;
      prmt.lastElementChild.onchange = () => {
        prmt.lastElementChild.previousElementSibling.disabled = !prmt.lastElementChild.value;
      }
      prmt.appendChild(document.createElement('button'));
      prmt.lastElementChild.appendChild(document.createTextNode('Send'));
      prmt.lastElementChild.onclick = () => {
        if (!prmt.lastElementChild.previousElementSibling.value) {
          return;
        }
        document.body.removeChild(prmt);
        resolve(prmt.lastElementChild.previousElementSibling.value);
      }
      document.body.appendChild(prmt);
    });
  }
  attachTo.confirm = async (text) => {
    return new Promise(resolve => {
      const prmt = document.createElement('div');
      prmt.setAttribute('id', 'prompt');
      prmt.appendChild(document.createElement('p'));
      prmt.firstElementChild.appendChild(document.createTextNode(text));
      prmt.appendChild(document.createElement('button'));
      prmt.lastElementChild.appendChild(document.createTextNode('Yes'));
      prmt.lastElementChild.onclick = () => {
        document.body.removeChild(prmt);
        resolve(true);
      }
      prmt.appendChild(document.createElement('button'));
      prmt.lastElementChild.appendChild(document.createTextNode('No'));
      prmt.lastElementChild.onclick = () => {
        document.body.removeChild(prmt);
        resolve(false);
      }
      document.body.appendChild(prmt);
    });
  }
  attachTo.alert = async (text) => {
    return new Promise(resolve => {
      const prmt = document.createElement('div');
      prmt.setAttribute('id', 'prompt');
      prmt.appendChild(document.createElement('p'));
      prmt.firstElementChild.appendChild(document.createTextNode(text));
      prmt.appendChild(document.createElement('button'));
      prmt.lastElementChild.appendChild(document.createTextNode('OK'));
      prmt.lastElementChild.onclick = () => {
        document.body.removeChild(prmt);
        resolve();
      }
      document.body.appendChild(prmt);
    });
  }
})(window.bjoernbuettner);
