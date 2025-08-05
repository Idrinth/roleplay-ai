(async () => {
  const apiHost = location.protocol + '//' + location.hostname + '/api/v1'
  const characterFiller = await (await fetch('/char-template.yaml')).text();
  const uuidRegexp = /^[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}$/i;
  const prompt = async (text, defaultText = '') => {
    return new Promise(resolve => {
      const prmt = document.createElement('div');
      prmt.setAttribute('id', 'prompt');
      prmt.appendChild(document.createElement('label'));
      prmt.firstElementChild.appendChild(document.createTextNode(text));
      prmt.appendChild(document.createElement('input'));
      prmt.lastElementChild.value = defaultText;
      prmt.lastElementChild.onchange = () => {
        prmt.lastElementChild.disabled = ! prmt.lastElementChild.previousElementSibling.value;
      }
      prmt.appendChild(document.createElement('button'));
      prmt.lastElementChild.appendChild(document.createTextNode('Send'));
      prmt.lastElementChild.onclick = () => {
        if (! prmt.lastElementChild.previousElementSibling.value) {
          return;
        }
        document.body.removeChild(prmt);
        resolve(prmt.lastElementChild.previousElementSibling.value);
      }
      document.body.appendChild(prmt);
    });
  }
  const confirm = async (text) => {
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
  const alert = async(text) => {
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
  const user = await (async () => {
    const user = await (await fetch(`${apiHost}/whoami`, {
      credentials: "include",
      method: "GET",
    })).json();
    if (!user.error) {
      return user;
    }
    const userId = await prompt("Enter your User-ID if you already have one.", "");
    if (userId) {
      if ((await (await fetch(`${apiHost}/login`, {
        credentials: "include",
        method: "POST",
        body: JSON.stringify({
          user_id: userId,
          password: await prompt("Enter your password.", "")
        }),
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      })).text()) !== "true") {
        await alert("Login failed!");
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
          password: await prompt("Enter a password for your account.", password)
        }),
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      })).text();
      await alert(`Your user-id is ${uuid} - please save that for logging in.`)
    }
    return await (await fetch(`${apiHost}/whoami`, {
      credentials: "include",
      method: "GET",
    })).json();
  })();

  document.getElementById('playername').innerText = (user.name ?? user.id);
  document.getElementById('playername').onclick = async () => {
    const previous = user.name ?? user.id;
    const name = await prompt("Enter a new name for yourself.", previous);
    const password = await prompt("Enter a new password for yourself.", "");
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
    const pathId = location.pathname.split('/')[2] ?? '';
    if (pathId.match(uuidRegexp)) {
      if (user.chats.length > 0) {
        for (const chat of user.chats) {
          if (chat.id === pathId) {
            return chat;
          }
        }
      }
    }
    if (user.chats.length > 0 && pathId !== 'new') {
      for (const chat of user.chats) {
        if (await confirm(`Do you want to continue chat '${chat.name}'?`)) {
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
    window.location = location.protocol + '//' + location.host + '/chat/new';
    return;
  } else if(chat.id !== (location.pathname.split('/')[2] ?? '')) {
    window.location = location.protocol + '//' + location.host + '/chat/' + chat.id
  }
  while (chat.id === chat.name || !chat.name) {
    chat.name = (await prompt("Enter a new name for your chat.", chat.name)) || chat.id;
    if (chat.name) {
      await fetch(`${apiHost}/chat/${chat.id}/name`, {
        method: 'POST',
        body: JSON.stringify({
          name: chat.name,
        }),
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        credentials: "include",
      });
    }
  }
  document.title = chat.name + ' | ' + document.title;
  
  for (const achat of user.chats) {
    document.getElementById('worlds').appendChild(document.createElement('li'));
    const world = document.getElementById('worlds').lastElementChild;
    world.appendChild(document.createElement('a'));
    world.lastElementChild.innerHTML = achat.name;
    world.lastElementChild.setAttribute('href', '/chat/' + achat.id);
    world.lastElementChild.setAttribute('data-id', achat.id);
    world.appendChild(document.createElement('span'));
    world.lastElementChild.appendChild(document.createTextNode('[D]'));
    world.lastElementChild.classList.add('button');
    world.lastElementChild.setAttribute('title', 'Delete chat');
    world.lastElementChild.onclick = async() => {
      if (await confirm(`Do you want to delete ${achat.name}?`)) {
        await fetch(
          `${apiHost}/chat/${achat.id}/delete`,
          {
            credentials: "include",
            method: "POST",
            signal: AbortSignal.timeout(10000),
          }
        );
        if (chat.id === achat.id) {
          window.location = location.protocol + '//' + location.hostname + '/chat';
          return;
        }
        document.getElementById('worlds').removeChild(world);
      }
    }
  }

  window.setInterval(async () => {
    try {
      const response = await fetch(
        `${apiHost}/chat/${chat.id}/active?${Date.now()}`,
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
      console.debug(e);
    }
    document.getElementById('send').disabled = true;
    document.getElementById('loader').setAttribute('style', '');
  }, 2500);
  const updateDocuments = await (async () => {
    const response = await fetch(`${apiHost}/chat/${chat.id}/documents`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      credentials: "include"
    });
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
          el.setAttribute('data-raw', el.content);
          document.body.appendChild(el);
        }
        document.getElementById('documents').lastElementChild.appendChild(document.createElement('span'));
        document.getElementById('documents').lastElementChild.lastElementChild.appendChild(document.createTextNode('[D]'));
        document.getElementById('documents').lastElementChild.lastElementChild.classList.add('button');
        document.getElementById('documents').lastElementChild.lastElementChild.setAttribute('title', 'Delete document');
        document.getElementById('documents').lastElementChild.lastElementChild.onclick = async (event) => {
          event.stopPropagation();
          if (await confirm("Do you want to delete this document?")) {
            await fetch(`${apiHost}/chat/${chat.id}/characters/${md_document._id['$oid']}/delete`, {
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
    const response = await fetch(`${apiHost}/chat/${chat.id}/characters`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      credentials: "include"
    });
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
          if (await confirm("Do you want to delete this character sheet?")) {
            await fetch(`${apiHost}/chat/${chat.id}/characters/${character._id['$oid']}/delete`, {
              method: 'POST',
              credentials: "include",
            });
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
      const response = await fetch(`${apiHost}/chat/${chat.id}`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({description: value}),
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
          document.getElementById('chat').lastElementChild.innerHTML = '<span class="gamemaster"></span>' + converter.makeHtml(json.message) + `<span class="duration">${Math.ceil(Date.now() / 1000 - now / 1000)}s</span>`;
          document.getElementById('chat').lastElementChild.classList.add('agent');
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
          document.getElementById('chat').lastElementChild.innerHTML = (message.role === 'agent' ? '<span class="gamemaster"></span>' : '') + converter.makeHtml(message.content);
          document.getElementById('chat').lastElementChild.classList.add(message.role);
        }
        if (json.messages.length === 0 && !document.getElementById('chat-entry').value && await confirm('Do you want help with your beginning scene?')) {
          const value = await fetch(`${apiHost}/chat/${chat.id}/starting-point-proposal`, {
            method: 'POST',
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              name: await prompt("What is your character's name?"),
              race: await prompt("What is your character's race?"),
              gender: await prompt("What is your character's gender?"),
              wear: await prompt("What does your character wear?"),
              profession: await prompt("What is your character's profession?"),
              location: await prompt("Where is your character?"),
              purpose: await prompt("What is their purpose there?"),
              mood: await prompt("What is your character's mood?"),
              weather: await prompt("What is your weather like?"),
              genre: await prompt("What genre does the world fall into?"),
              world: await prompt("What is the world like? Please provide keywords separated by comma."),
            }),
            credentials: "include",
          });
          document.getElementById('chat-entry').value = document.getElementById('chat-entry').value || (await value.json()).message;
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
            if (await confirm("Do you want to save this modified character sheet?")) {
              const id = charactersheetElement.getAttribute('data-id');
              await fetch(`${apiHost}/chat/${chat.id}/characters/${id}`, {
                method: 'POST',
                headers: {
                  'Accept': 'application/json',
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify(jsyaml.load(charactersheetElement.value)),
                credentials: "include",
              });
            }
          }
        } else if (charactersheetElement.value) {
          if (await confirm("Do you want to save this new character sheet?")) {
            await fetch(`${apiHost}/chat/${chat.id}/characters`, {
              method: 'POST',
              headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
              },
              body: JSON.stringify(jsyaml.load(charactersheetElement.value)),
              credentials: "include",
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
            if (await confirm("Do you want to save this modified document?")) {
              const id = documentElement.getAttribute('data-id');
              await fetch(`${apiHost}/chat/${chat.id}/documents/${id}`, {
                method: 'POST',
                headers: {
                  'Accept': 'application/json',
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({content: documentElement.value, name: documentElement.getAttribute('data-name')},),
                credentials: "include",
              });
            }
          }
        } else if (documentElement.value) {
          if (await confirm("Do you want to save this new document?")) {
            await fetch(`${apiHost}/chat/${chat.id}/documents`, {
              method: 'POST',
              headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                content: documentElement.value,
                name: prompt("What is your document named?")
              },),
              credentials: "include",
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
      document.getElementById('world').previousElementSibling.setAttribute('title', keywords.join("\n"))
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
    document.getElementById('world').previousElementSibling.setAttribute('title', keywords.join("\n"))
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
})();
