((root) => {
  const createModal = (text: string, useLabel: boolean = false) => {
    const prmt = document.createElement('div');
    prmt.setAttribute('id', 'prompt');
    const label = document.createElement(useLabel ? 'label' : 'p');
    prmt.appendChild(label);
    label.appendChild(document.createTextNode(text));
    return prmt;
  }
  root.prompt = async (text: string, defaultText: string = ''): Promise<string> => {
    return new Promise(resolve => {
      const prmt = createModal(text, true);
      const input = document.createElement('input');
      input.onkeyup = (event: KeyboardEvent) => {
        if (event.key === 'Enter') {
          if (!input.value) {
            return;
          }
          document.body.removeChild(prmt);
          resolve(input.value);
        }
      }
      prmt.appendChild(input);
      input.value = defaultText;
      prmt.appendChild(root.button('Send', 'Send changes', () => {
        if (!input.value) {
          return;
        }
        document.body.removeChild(prmt);
        resolve(input.value);
      }, true));
      document.body.appendChild(prmt);
      input.focus();
    });
  }
  root.selectFrom = async (text: string, options: string[], defaultText: string = ''): Promise<string> => {
    return new Promise(resolve => {
      const prmt = createModal(text, true);
      const select = document.createElement('select');
      select.onchange = (event: Event) => {
        if (select.value) {
          document.body.removeChild(prmt);
          resolve(select.value);
        }
      }
      options.unshift('');
      for (const option of options) {
        const opt = document.createElement('option');
        opt.value = option;
        opt.appendChild(document.createTextNode(text));
        select.appendChild(opt);
        if (defaultText === option) {
          opt.selected = true;
        }
      }
      prmt.appendChild(select);
      select.value = defaultText;
      prmt.appendChild(root.button('Send', 'Send changes', () => {
        if (!select.value) {
          return;
        }
        document.body.removeChild(prmt);
        resolve(select.value);
      }, true));
      document.body.appendChild(prmt);
      select.focus();
    });
  }
  root.confirm = async (text: string): Promise<boolean> => {
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
  root.alert = async (text: string): Promise<void> => {
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
