(async () => {
  const apiHost = location.protocol + '//' + location.hostname + '/api/v1'
  const characterFiller = await (await fetch('/char-template.yaml')).text();
  const uuidRegexp = /^[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}$/i;
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
        document.getElementById('characters').removeChild(document.getElementById('characters').lastChild);
      }
      for (const character of json.characters) {
        document.getElementById('characters').appendChild(document.createElement('li'));
        document.getElementById('characters').lastChild.appendChild(document.createElement('span'));
        document.getElementById('characters').lastChild.lastChild.appendChild(document.createTextNode(character.name.taken));
        document.getElementById('characters').lastChild.appendChild(document.createElement('span'));
        document.getElementById('characters').lastChild.lastChild.appendChild(document.createTextNode('[E]'));
        document.getElementById('characters').lastChild.lastChild.classList.add('button');
        document.getElementById('characters').lastChild.lastChild.setAttribute('title', 'Edit character');
        document.getElementById('characters').lastChild.lastChild.onclick = (event) => {
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
        document.getElementById('characters').lastChild.appendChild(document.createElement('span'));
        document.getElementById('characters').lastChild.lastChild.appendChild(document.createTextNode('[D]'));
        document.getElementById('characters').lastChild.lastChild.classList.add('button');
        document.getElementById('characters').lastChild.lastChild.setAttribute('title', 'Delete character');
        document.getElementById('characters').lastChild.lastChild.onclick = async (event) => {
          event.stopPropagation();
          if (confirm("Do you want to delete this character sheet?")) {
            await fetch(`${apiHost}/chat/${chat.id}/characters/${character._id['$oid']}`, {
              method: 'DELETE',
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
    document.getElementById('chat').lastChild.innerHTML = converter.makeHtml(value);
    document.getElementById('chat').lastChild.classList.add('user');
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
  document.getElementById('logo').onclick = () => {
    document.getElementsByTagName('html')[0]?.classList.toggle('inverted-colors');
    window.localStorage && window.localStorage.setItem(
      'prefered-color-scheme',
      document.getElementsByTagName('html')[0]?.classList.contains('inverted-colors') ? 'light' : 'dark',
    );
  }
  document.getElementById('imprint-open').onclick = () => {
    document.getElementById('imprint').removeAttribute('style');
  }
})();
