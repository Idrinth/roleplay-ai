(async () => {
  const apiHost = location.protocol + '//' + location.hostname + '/api/v1'
  const characterFiller = await (await fetch('/char-template.yaml')).text();
  const uuidRegexp = /^[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}$/i;
  const createEl = ({ tag = 'div', cla = [], txt = '', src = '', parent, val = '', type = '', id } = {}) => {
    const el = document.createElement(tag);
    if (Array.isArray(cla)) {
      cla.forEach(className => el.classList.add(className));
    } else if (typeof cla === 'string') {
      el.classList.add(cla);
    }

    txt ? el.textContent = txt : null;
    src ? el.src = src : null;
    val ? el.value = val : null;
    type ? el.setAttribute('type', type) : null;
    id >= 0 ? el.id = id : null;
    if (parent) {
      if (typeof parent === 'string') {
        document.querySelector(parent)?.appendChild(el);
      } else if (parent instanceof HTMLElement) {
        parent.appendChild(el);
      }
    }

    return el;
  }
  const user = await (async () => {
    const user = await (await fetch(`${apiHost}/whoami`, {
      credentials: "include",
      method: "GET",
    })).json();
    if (!user.error) {
      return user;
    }
    const userId = prompt("Enter your User-ID if you already have one.", "");
    if (userId) {
      if ((await (await fetch(`${apiHost}/login`, {
        credentials: "include",
        method: "POST",
        body: JSON.stringify({
          user_id: userId,
          password: prompt("Enter your password.", "")
        }),
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      })).text()) !== "true") {
        alert("Login failed!");
        location.reload()
        return;
      }
    } else {
      const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890".split("")
      const password = chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)]
        + chars[Math.floor(Math.random() * chars.length)];
      const uuid = await (await fetch(`${apiHost}/register`, {
        credentials: "include",
        method: "POST",
        body: JSON.stringify({
          password: prompt("Enter a password for your account.", password)
        }),
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      })).text();
      alert(`Your user-id is ${uuid} - please save that for logging in. Right now the password is hardcoded as example.`)
    }
    return await (await fetch(`${apiHost}/whoami`, {
      credentials: "include",
      method: "GET",
    })).json();
  })();
  console.log(user);

  document.getElementById('playername').innerText = (user.name ?? user.id);
  document.getElementById('playername').onclick = async () => {
    const previous = user.name ?? user.id;
    const name = prompt("Enter a new name for yourself.", previous);
    const password = prompt("Enter a new password for yourself.", "");
    const data = {};
    let changed = false;
    if (name && name !== previous) {
      data.username = name;
      changed = true;
    }
    if (password) {
      changed = true;
      data.password = password;
    }
    if (changed) {
      await (await fetch(`${apiHost}/me`, {
        credentials: "include",
        method: "POST",
        body: JSON.stringify(data),
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      }));
      document.getElementById('playername').innerText = name;
    }
  }

  const chat = await (async () => {
    if (location.hash.replace(/[^0-9a-f-]+/g, '').match(uuidRegexp)) {
      const likely = location.hash.replace(/[^0-9a-f-]+/g, '');
      if (user.chats.length > 0) {
        for (const chat of user.chats) {
          if (chat.id === likely) {
            return chat;
          }
        }
      }
    }
    if (user.chats.length > 0) {
      for (const chat of user.chats) {
        if (confirm(`Do you want to continue chat '${chat.name}'?`)) {
          return chat;
        }
      }
    }
    const chatId = (await (await fetch(`${apiHost}/new`, {
      credentials: "include",
      method: "GET",
    })).json()).chat ?? "";
    return {
      id: chatId,
      name: chatId,
    }
  })();

  if (!chat.id || !chat.id.match(uuidRegexp)) {
    window.location = location.protocol + '//' + location.host;
    return;
  }
  location.hash = `#${chat.id}`;
  while (chat.id === chat.name) {
    chat.name = prompt("Enter a new name for your chat.", chat.name) || chat.id;
    await fetch(`${apiHost}/chat/${chat.id}`, {
      method: 'POST',
      body: JSON.stringify({
        name: chat.name,
      }),
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      credentials: "include",
    })
  }
  document.title = chat.name + ' | ' + document.title;

  window.setInterval(async () => {
    try {
      const response = await fetch(
        `${apiHost}/chat/${chat.id}/active`,
        {
          credentials: "include",
          method: "GET",
          signal: AbortSignal.timeout(2400),
        }
      );
      if (response.ok) {
        const active = (await response.json()).active;
        if (!active) {
          document.getElementById('send').disabled = false;
          document.getElementById('loader').setAttribute('style', 'display: none');
          return;
        }
      }
    } catch (e) {
      //this is expected
    }
    document.getElementById('send').disabled = true;
    document.getElementById('loader').setAttribute('style', '');
  }, 2500);

  const updateCharacters = async () => {
    async function requestCharacters() {
      const url = `${apiHost}/chat/${chat.id}/characters`
      const payload = {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        credentials: "include"
      };

      try {
        const charactersRequest = await fetch(url, payload);
        const characters = await charactersRequest.json();
        return characters;
      } catch (e) {
        console.log(e);
        return false;
      }
    }
    function clearCharactersList() {
      const allCharacterBtns = document.querySelectorAll('#character-button')
      if (!allCharacterBtns.length) return;
      allCharacterBtns.forEach(character => character.dispatchEvent(new Event('disappear')))
    }
    function renderCharacter(place, character) {
      const name = character.name.taken;

      const characterContainer = create({ tag: 'li', cla: 'file-dropdown-item', id: 'character-button', parent: place });
      create({ tag: 'img', cla: 'character-icon', src: './images/default.png', parent: characterContainer });
      create({ tag: 'span', cla: 'file-name', txt: name, parent: characterContainer });
      const optionsMenu = create({ tag: 'div', cla: 'options-menu', parent: characterContainer });
      create({ tag: 'img', cla: 'dropdown-icon', src: './images/ellipsis.png', parent: optionsMenu });
      const optionsDropdown = create({ tag: 'div', cla: 'options-dropdown', parent: optionsMenu });
      const editButton = create({ tag: 'div', cla: 'option-button-container', parent: optionsDropdown });
      create({ tag: 'img', cla: 'option-icon', src: './images/edit.png', parent: editButton });
      create({ tag: 'span', txt: 'Edit', parent: editButton });
      const deleteButton = create({ tag: 'div', cla: 'option-button-container', parent: optionsDropdown });
      create({ tag: 'img', cla: 'option-icon', src: './images/delete.png', parent: deleteButton });
      create({ tag: 'span', txt: 'Delete', parent: deleteButton });


      const disappear = () => {
        editButton.removeEventListener('click', editCharacter)
        deleteButton.removeEventListener('click', deleteCharacter)
        characterContainer.remove();
      }; characterContainer.addEventListener('disappear', disappear);

      const editCharacter = () => {
        const char = { ...character };
        char._id = undefined;
        characterSheetEditor.setAttribute('data-id', character._id['$oid']);
        characterSheetEditor.value = jsyaml.dump(char);
        characterSheetEditor.setAttribute('data-raw', characterSheetEditor.value);
        document.body.appendChild(el);
      }; editButton.addEventListener('click', editCharacter);

      const deleteCharacter = async () => {
        if (confirm("Do you want to delete this character sheet?")) {
          const url = `${apiHost}/chat/${chat.id}/characters/${character._id['$oid']}`
          const payload = {
            method: 'DELETE',
            credentials: "include",
          }
          await fetch(url, payload);
          await updateCharacters();
        }
        deleteUiComponent();
      }; deleteButton.addEventListener('click', deleteCharacter);
    }
    function renderCharacters(characters) {
      const charactersList = document.querySelector("#characters-list");
      const { characters: charArray } = characters;
      charArray.forEach(char => renderCharacter(charactersList, char))
    }
    try {
      const characters = await requestCharacters()
      if (!characters) {
        alert("Sadly, your characters couldn't be loaded. Try again later.")
        return;
      }
      clearCharactersList();
      renderCharacters(characters);
      return true;
    } catch (e) {
      console.log("Error when attempting to update characters. Please, try again.")
      return false;
    }
  }
  document.getElementById('send').addEventListener('click', async function () {
    const now = Date.now();
    const value = document.getElementById('chat-entry').value;
    if (!value) {
      return;
    }
    const converter = new showdown.Converter();
    document.getElementById('send').disabled = true;
    document.getElementById('chat-entry').value = '';
    document.getElementById('chat').appendChild(document.createElement('li'));
    document.getElementById('chat').lastChild.innerHTML = converter.makeHtml(value);
    document.getElementById('chat').lastChild.classList.add('user');
    try {
      const response = await fetch(`${apiHost}/chat/${chat.id}`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ description: value }),
        credentials: "include",
      });
      if (response.ok) {
        const json = await response.json();
        if (json.error) {
          console.error(json.error);
        } else if (json.exception) {
          console.error(json.exception);
        } else {
          document.getElementById('chat').appendChild(document.createElement('li'));
          document.getElementById('chat').lastChild.innerHTML = '<span class="gamemaster"></span>' + converter.makeHtml(json.message) + `<span class="duration">${Math.ceil(Date.now() / 1000 - now / 1000)}s</span>`;
          document.getElementById('chat').lastChild.classList.add('agent');
        }
      }
    } catch (e) {
      console.error(e);
    }
  });
  await (async () => {
    const response = await fetch(`${apiHost}/chat/${chat.id}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      credentials: "include",
    });
    if (response.ok) {
      const converter = new showdown.Converter();
      const json = await response.json();
      if (json.error) {
        console.error(json.error);
      } else if (json.exception) {
        console.error(json.exception);
      } else {
        for (const message of json.messages) {
          document.getElementById('chat').appendChild(document.createElement('li'));
          document.getElementById('chat').lastChild.innerHTML = (message.role === 'agent' ? '<span class="gamemaster"></span>' : '') + converter.makeHtml(message.content);
          document.getElementById('chat').lastChild.classList.add(message.role);
        }
      }
    }
  })();
  document.body.onclick = async (event) => {
    const el = document.getElementById('charactersheet');
    if (el) {
      if (event.target !== el) {
        if (el.hasAttribute('data-id')) {
          if (el.value && el.getAttribute('data-raw') !== el.value) {
            if (confirm("Do you want to save this modified character sheet?")) {
              const id = el.getAttribute('data-id');
              await fetch(`${apiHost}/chat/${chat.id}/characters/${id}`, {
                method: 'POST',
                headers: {
                  'Accept': 'application/json',
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify(jsyaml.load(el.value)),
                credentials: "include",
              });
            }
          }
        } else if (el.value) {
          if (confirm("Do you want to save this new character sheet?")) {
            await fetch(`${apiHost}/chat/${chat.id}/characters`, {
              method: 'POST',
              headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
              },
              body: JSON.stringify(jsyaml.load(el.value)),
              credentials: "include",
            })
          }
        }
        document.body.removeChild(el);
        await updateCharacters();
      }
    }
    document.getElementById('imprint').setAttribute('style', 'display:none');
  }
  await updateCharacters();
  document.getElementById('add-character').onclick = async (event) => {
    event.stopPropagation();
    const el = document.createElement('textarea');
    el.setAttribute('id', 'charactersheet');
    el.value = characterFiller;
    document.body.appendChild(el);
  }
  await (async () => {
    const response = await fetch(`${apiHost}/chat/${chat.id}/world`, {
      method: "GET",
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      credentials: "include",
    });
    if (response.ok) {
      const keywords = (await response.json()).world;
      document.getElementById('world-button').setAttribute('title', keywords.join("\n"))
      document.getElementById('world').setAttribute('data-original', JSON.stringify(keywords))
      document.getElementById('world').value = keywords.join(", ")
    }
  })();
  document.getElementById("world").onchange = () => {
    const keywords = document.getElementById('world').value.split(",").map((keyword) => {
      return keyword.replace(/^\s+|\s+$/g, '').replace(/\s{2,}/g, ' ')
    }).filter((keyword) => {
      return !!keyword;
    });
    keywords.sort();
    const oldKeywords = JSON.parse(document.getElementById('world').getAttribute('data-original')).sort();
    if (keywords.join() === oldKeywords.join()) {
      return;
    }
    document.getElementById('world').setAttribute('data-original', JSON.stringify(keywords))
    document.getElementById('world-button').setAttribute('title', keywords.join("\n"))
    fetch(`${apiHost}/chat/${chat.id}/world`, {
      method: "PUT",
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        keywords,
      }),
      credentials: "include",
    })
  }
  if (window.matchMedia && !window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.getElementsByTagName('html')[0]?.classList.toggle('inverted-colors');
  }
  if (window.localStorage) {
    const preferedColorScheme = window.localStorage.getItem('prefered-color-scheme');
    if (preferedColorScheme === 'dark') {
      document.getElementsByTagName('html')[0]?.classList.remove('inverted-colors');
    } else if (preferedColorScheme === 'light') {
      document.getElementsByTagName('html')[0]?.classList.add('inverted-colors');
    }
    window.localStorage.setItem('prefered-color-scheme', document.getElementsByTagName('html')[0]?.classList.contains('inverted-colors') ? 'light' : 'dark');
  }
  document.getElementById('theme-changer').onclick = () => {
    document.getElementsByTagName('html')[0]?.classList.toggle('inverted-colors');
    window.localStorage && window.localStorage.setItem(
      'prefered-color-scheme',
      document.getElementsByTagName('html')[0]?.classList.contains('inverted-colors') ? 'light' : 'dark',
    );
  }
  document.getElementById('imprint-open').onclick = (event) => {
    event.preventDefault();
    event.stopPropagation();
    document.getElementById('imprint').removeAttribute('style');
  }
})();
