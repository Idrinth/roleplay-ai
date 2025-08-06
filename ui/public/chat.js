(async (root) => {
  const characterFiller = await (await fetch('/char-template.yaml')).text();
  const user = await (async () => {
    const user = await root.getFromAPI('whoami', 'GET');
    if (!user.error) {
      return user;
    }
    if (await root.confirm("Do you already have an account?")) {
      const userId = await root.prompt("Enter your User-ID.", "");
      if (await root.getFromAPI(`login`, 'POST', {
          user_id: userId,
          password: await root.prompt("Enter your password.", "")
        }, 10000, false) !== "true") {
        await alert("Login failed!");
        location.reload()
        return;
      }
    } else {
      const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890".split("")
      const randChar = () => chars[Math.floor(Math.random() * chars.length)];
      const password = randChar()
        + randChar()
        + randChar()
        + randChar()
        + randChar()
        + randChar()
        + randChar()
        + randChar()
        + randChar()
        + randChar()
        + randChar()
        + randChar()
        + randChar()
        + randChar()
        + randChar()
        + randChar()
        + randChar()
        + randChar()
        + randChar()
        + randChar()
        + randChar()
        + randChar()
        + randChar()
        + randChar();
      const uuid = await root.getFromAPI(`register`, 'POST', {
          password: await root.prompt("Enter a password for your account.", password)
        }, 10000, false);
      await alert(`Your user-id is ${uuid} - please save that for logging in.`)
    }
    return root.getFromAPI(`whoami`, 'GET');
  })();

  document.getElementById('playername').innerText = (user.name ?? user.id);
  document.getElementById('playername').onclick = async () => {
    const previous = user.name ?? user.id;
    const name = await root.prompt("Enter a new name for yourself.", previous);
    const password = await root.prompt("Enter a new password for yourself.", "");
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
      await root.getFromAPI(`${root.apiEndpoint}/me`, 'POST', data);
      document.getElementById('playername').innerText = name;
    }
  }

  const chat = await (async () => {
    const pathId = location.pathname.split('/')[2] ?? '';
    if (user.chats.length > 0) {
      for (const chat of user.chats) {
        if (chat.id === pathId) {
          return chat;
        }
      }
    }
    if (user.chats.length > 0 && pathId !== 'new') {
      for (const chat of user.chats) {
        if (await root.confirm(`Do you want to continue chat '${chat.name}'?`)) {
          return chat;
        }
      }
    }
    const chatId = (await root.getFromAPI(`new`, {
      credentials: "include",
      method: "GET",
    })).chat ?? "";
    return {
      id: chatId,
      name: chatId,
    }
  })();

  if(chat.id !== (location.pathname.split('/')[2] ?? '')) {
    window.location = location.protocol + '//' + location.host + '/chat/' + chat.id
  }
  while (chat.id === chat.name || !chat.name) {
    chat.name = (await root.prompt("Enter a new name for your chat.", chat.name)) || chat.id;
    if (chat.name) {
      await root.getFromAPI(`chat/${chat.id}/name`, 'POST', {
        name: chat.name,
      });
    }
  }
  document.title = chat.name + ' | ' + document.title;
  
  root.listExistingChats(user.chats, chat.id)

  window.setInterval(async () => {
    try {
      const response = await root.getFromAPI(
        `chat/${chat.id}/active?${Date.now()}`,
        'GET',
        null,
        2400,
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
      console.debug(e);
    }
    document.getElementById('send').disabled = true;
    document.getElementById('loader').setAttribute('style', '');
  }, 2500);
  const updateDocuments = await (async () => {
    const response = await root.getFromAPI(`chat/${chat.id}/documents`, 'GET');
    if (response.ok) {
      const json = await response.json();
      if (json.error) {
        console.error(json.error);
        return;
      }
      if (json.exception) {
        console.error(json.exception);
        return;
      }
      while (document.getElementById('documents').children.length > 2) {
        document.getElementById('documents').removeChild(document.getElementById('characters').lastElementChild);
      }
      for (const md_document of json.documents) {
        document.getElementById('documents').appendChild(document.createElement('li'));
        document.getElementById('documents').lastElementChild.appendChild(document.createElement('span'));
        document.getElementById('documents').lastElementChild.lastElementChild.appendChild(document.createTextNode(md_document.name));
        document.getElementById('documents').lastElementChild.appendChild(document.createElement('span'));
        document.getElementById('documents').lastElementChild.lastElementChild.appendChild(document.createTextNode('[E]'));
        document.getElementById('documents').lastElementChild.lastElementChild.classList.add('button');
        document.getElementById('documents').lastElementChild.lastElementChild.setAttribute('title', 'Edit document');
        document.getElementById('documents').lastElementChild.lastElementChild.onclick = (event) => {
          event.stopPropagation();
          const el = document.createElement('textarea');
          el.setAttribute('id', 'document')
          const doc = {...md_document};
          doc._id = undefined;
          el.setAttribute('data-id', md_document.id['$oid']);
          el.setAttribute('data-name', doc.name);
          el.value = doc.content;
          el.setAttribute('data-raw', doc.content);
          document.body.appendChild(el);
        }
        document.getElementById('documents').lastElementChild.appendChild(document.createElement('span'));
        document.getElementById('documents').lastElementChild.lastElementChild.appendChild(document.createTextNode('[D]'));
        document.getElementById('documents').lastElementChild.lastElementChild.classList.add('button');
        document.getElementById('documents').lastElementChild.lastElementChild.setAttribute('title', 'Delete document');
        document.getElementById('documents').lastElementChild.lastElementChild.onclick = async (event) => {
          event.stopPropagation();
          if (await root.confirm("Do you want to delete this document?")) {
            await root.getFromAPI(`${root.apiEndpoint}/chat/${chat.id}/characters/${md_document._id['$oid']}/delete`, {
              method: 'POST',
              credentials: "include",
            });
            await updateDocuments();
          }
        }
      }
    }
  })
  const updateCharacters = async () => {
    const response = await root.getFromAPI(`chat/${chat.id}/characters`, 'GET');
    if (response.ok) {
      const json = await response.json();
      if (json.error) {
        console.error(json.error);
        return;
      }
      if (json.exception) {
        console.error(json.exception);
        return;
      }
      while (document.getElementById('characters').children.length > 1) {
        document.getElementById('characters').removeChild(document.getElementById('characters').lastElementChild);
      }
      for (const character of json.characters) {
        document.getElementById('characters').appendChild(document.createElement('li'));
        document.getElementById('characters').lastElementChild.appendChild(document.createElement('span'));
        document.getElementById('characters').lastElementChild.lastElementChild.appendChild(document.createTextNode(character.name.taken));
        document.getElementById('characters').lastElementChild.appendChild(document.createElement('span'));
        document.getElementById('characters').lastElementChild.lastElementChild.appendChild(document.createTextNode('[E]'));
        document.getElementById('characters').lastElementChild.lastElementChild.classList.add('button');
        document.getElementById('characters').lastElementChild.lastElementChild.setAttribute('title', 'Edit character');
        document.getElementById('characters').lastElementChild.lastElementChild.onclick = (event) => {
          event.stopPropagation();
          const el = document.createElement('textarea');
          el.setAttribute('id', 'charactersheet')
          const char = {...character};
          char._id = undefined;
          el.setAttribute('data-id', character._id['$oid']);
          el.value = jsyaml.dump(char);
          el.setAttribute('data-raw', el.value);
          document.body.appendChild(el);
        }
        document.getElementById('characters').lastElementChild.appendChild(document.createElement('span'));
        document.getElementById('characters').lastElementChild.lastElementChild.appendChild(document.createTextNode('[D]'));
        document.getElementById('characters').lastElementChild.lastElementChild.classList.add('button');
        document.getElementById('characters').lastElementChild.lastElementChild.setAttribute('title', 'Delete character');
        document.getElementById('characters').lastElementChild.lastElementChild.onclick = async (event) => {
          event.stopPropagation();
          if (await root.confirm("Do you want to delete this character sheet?")) {
            await root.getFromAPI(`chat/${chat.id}/characters/${character._id['$oid']}/delete`, 'POST');
            await updateCharacters();
          }
        }
      }
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
    document.getElementById('chat').lastElementChild.innerHTML = converter.makeHtml(value);
    document.getElementById('chat').lastElementChild.classList.add('user');
    try {
      const response = await root.getFromAPI(`chat/${chat.id}`, 'POST', {description: value});
      if (response.ok) {
        const json = await response.json();
        if (json.error) {
          console.error(json.error);
        } else if (json.exception) {
          console.error(json.exception);
        } else {
          document.getElementById('chat').appendChild(document.createElement('li'));
          document.getElementById('chat').lastElementChild.innerHTML = '<span class="gamemaster"></span>' + converter.makeHtml(json.message) + `<span class="duration">${Math.ceil(Date.now() / 1000 - now / 1000)}s</span>`;
          document.getElementById('chat').lastElementChild.classList.add('agent');
        }
      }
    } catch (e) {
      console.error(e);
    }
  });
  await (async () => {
    const response = root.getFromAPI(`chat/${chat.id}`, 'GET', {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
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
          document.getElementById('chat').lastElementChild.innerHTML = (message.role === 'agent' ? '<span class="gamemaster"></span>' : '') + converter.makeHtml(message.content);
          document.getElementById('chat').lastElementChild.classList.add(message.role);
        }
        if (json.messages.length === 0 && !document.getElementById('chat-entry').value && await root.confirm('Do you want help with your beginning scene?')) {
          const value = await root.getFromAPI(`chat/${chat.id}/starting-point-proposal`, 'POST', {
            name: await root.prompt("What is your character's name?"),
            race: await root.prompt("What is your character's race?"),
            gender: await root.prompt("What is your character's gender?"),
            wear: await root.prompt("What does your character wear?"),
            profession: await root.prompt("What is your character's profession?"),
            location: await root.prompt("Where is your character?"),
            purpose: await root.prompt("What is their purpose there?"),
            mood: await root.prompt("What is your character's mood?"),
            weather: await root.prompt("What is your weather like?"),
            genre: await root.prompt("What genre does the world fall into?"),
            world: await root.prompt("What is the world like? Please provide keywords separated by comma."),
          });
          document.getElementById('chat-entry').value = (await value.json()).message;
        }
      }
    }
  })();
  document.body.onclick = async (event) => {
    const charactersheetElement = document.getElementById('charactersheet');
    const documentElement = document.getElementById('document');
    if (charactersheetElement) {
      if (event.target !== charactersheetElement) {
        if (charactersheetElement.hasAttribute('data-id')) {
          if (charactersheetElement.value && charactersheetElement.getAttribute('data-raw') !== charactersheetElement.value) {
            if (await root.confirm("Do you want to save this modified character sheet?")) {
              const id = charactersheetElement.getAttribute('data-id');
              await root.getFromAPI(`chat/${chat.id}/characters/${id}`, {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
              });
            }
          }
        } else if (charactersheetElement.value) {
          if (await root.confirm("Do you want to save this new character sheet?")) {
            await root.getFromAPI(`chat/${chat.id}/characters`, 'POST', {
              'Accept': 'application/json',
              'Content-Type': 'application/json',
            })
          }
        }
        document.body.removeChild(charactersheetElement);
        await updateCharacters();
      }
    }
    if (documentElement) {
      if (event.target !== documentElement) {
        if (documentElement.hasAttribute('data-id')) {
          if (documentElement.value && documentElement.getAttribute('data-raw') !== documentElement.value) {
            if (await root.confirm("Do you want to save this modified document?")) {
              const id = documentElement.getAttribute('data-id');
              await root.getFromAPI(`chat/${chat.id}/documents/${id}`, 'POST', {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
              });
            }
          }
        } else if (documentElement.value) {
          if (await root.confirm("Do you want to save this new document?")) {
            await root.getFromAPI(`chat/${chat.id}/documents`, 'POST', {
              content: documentElement.value,
              name: prompt("What is your document named?")
            })
          }
        }
        document.body.removeChild(documentElement);
        await updateCharacters();
      }
    }
  }
  await updateCharacters();
  document.getElementById('add-character').onclick = async (event) => {
    event.stopPropagation();
    const el = document.createElement('textarea');
    el.setAttribute('id', 'charactersheet');
    el.value = characterFiller;
    document.body.appendChild(el);
  }
  await updateDocuments();
  document.getElementById('add-document').onclick = async (event) => {
    event.stopPropagation();
    const el = document.createElement('textarea');
    el.setAttribute('id', 'document');
    el.value = '';
    document.body.appendChild(el);
  }
  await (async () => {
    const response = root.getFromAPI(`chat/${chat.id}/world`,'GET');
    if (!response.world) {
      return;
    }
    const keywords = response.world;
    document.getElementById('world').previousElementSibling.setAttribute('title', keywords.join("\n"))
    document.getElementById('world').setAttribute('data-original', JSON.stringify(keywords))
    document.getElementById('world').value = keywords.join(", ")
  })();
  document.getElementById("world").onchange = () => {
    const keywords = document.getElementById('world').value.split(",").map((keyword) => {
      return keyword.trim()
    }).filter((keyword) => {
      return !!keyword;
    });
    keywords.sort();
    const oldKeywords = JSON.parse(document.getElementById('world').getAttribute('data-original')).sort();
    if (keywords.join() === oldKeywords.join()) {
      return;
    }
    document.getElementById('world').setAttribute('data-original', JSON.stringify(keywords))
    document.getElementById('world').previousElementSibling.setAttribute('title', keywords.join("\n"))
    root.getFromAPI(`chat/${chat.id}/world`, 'PUT', {
      keywords,
    });
  }
})(window.bjoernbuettner);
