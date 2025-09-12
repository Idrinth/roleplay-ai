(async (root) => {
  const characterFiller = await (await fetch('/char-template.yaml')).text();
  // if the purifier is not there, the only one suffering is the user themselves
  const purifier = window.DOMPurify?.sanitize ?? ((html: string) => {return html;});
  const user = await (async () => {
    const user = await root.getUser();
    if (user) {
      return user;
    }
    if (await root.confirm("Do you already have an account?")) {
      const userId = await root.prompt("Enter your User-ID.", "");
      const login = await root.getFromAPI(`login`, 'POST', {
          user_id: userId,
          password: await root.prompt("Enter your password.", "")
        }, 10000) as {success?:boolean};
      if (!login?.success) {
        await root.alert("Login failed!");
        location.reload()
        return;
      }
      return await root.getFromAPI(`whoami`, 'GET');
    }
    const uuid = (await root.getFromAPI(`register`, 'POST', {
        password: await root.prompt("Enter a password for your account.", root.password())
      }, 10000) as {user?: string}).user ?? false;
    if (uuid === false) {
      await root.alert("Registration failed!");
      location.reload()
      return;
    }
    await root.alert(`Your user-id is ${uuid} - please save that for logging in.`);
    return await root.getFromAPI(`whoami`, 'GET');
  })() as {name: string, id: string, chats: {id: string, name: string}[]};

  const playername = document.getElementById('playername');
  if (playername) {
    playername.innerText = user.name ?? user.id;
    playername.onclick = async () => {
      const previous = user.name ?? user.id;
      const name = await root.prompt("Enter a new name for yourself.", previous);
      const password = await root.prompt("Enter a new password for yourself.", "");
      const data : {
        username?: string,
        password: string,
      } = {password};
      if (name !== previous) {
        data.username = name;
      }
      await root.getFromAPI(`me`, 'POST', data);
      playername.innerText = name;
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
    const newChat = await root.getFromAPI(`new`, 'GET');
    if (root.isObjectWithProperty(newChat, 'chat')) {
      return {
        id: newChat['chat'] as string,
        name: newChat['chat'] as string,
      }
    }
    return {
      id: 'new',
      name: 'New Chat',
    }
  })();

  if(chat.id !== (location.pathname.split('/')[2] ?? '')) {
    window.location.assign(location.protocol + '//' + location.host + '/chat/' + chat.id);
    return;
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

  const sendButton = document.getElementById('send') as  null|HTMLButtonElement;
  const documents = document.getElementById('documents');
  const characters = document.getElementById('characters');
  const world = document.getElementById('world') as HTMLInputElement|null;
  const chatWrapper = document.getElementById('chat');
  const chatEntry = document.getElementById('chat-entry') as HTMLTextAreaElement|null;
  if (!sendButton || !documents || !characters || !world || !chatWrapper || !chatEntry || !window?.showdown?.Converter || !window?.jsyaml?.load) {
    return;
  }
  const converter = new window.showdown.Converter();
  const updateDocuments = async () => {
    const json = await root.getFromAPI(`chat/${chat.id}/documents`, 'GET');
    while (documents.children.length > 2) {
      const lastElementChild = documents.lastElementChild;
      if (lastElementChild) {
        documents.removeChild(lastElementChild);
      }
    }
    if (root.isObjectWithProperty(json, 'documents') && Array.isArray(json['documents'])) {
      for (const md_document of (json as {documents: {name: string,content: string, id: string}[]}).documents) {
        const doc = document.createElement('li');
        doc.setAttribute('class', 'name-edit-delete');
        documents.appendChild(doc);
        const docName = document.createElement('span');
        doc.appendChild(docName);
        docName.appendChild(document.createTextNode(md_document.name));
        doc.appendChild(root.button('[E]', 'Edit document', (event: MouseEvent) => {
          event.stopPropagation();
          const el = document.createElement('textarea');
          el.setAttribute('id', 'document')
          el.setAttribute('data-id', md_document.id);
          el.setAttribute('data-name', md_document.name);
          el.value = md_document.content;
          el.setAttribute('data-raw', md_document.content);
          document.body.appendChild(el);
        }));
        doc.appendChild(root.button('[D]', 'Delete document', async (event: MouseEvent) => {
          event.stopPropagation();
          if (await root.confirm("Do you want to delete this document?")) {
            await root.getFromAPI(`chat/${chat.id}/documents/${md_document.id}/delete`, 'POST');
            await updateDocuments();
          }
        }));
      }
    }
  }
  const updateCharacters = async () => {
    const json = await root.getFromAPI(`chat/${chat.id}/characters`, 'GET');
    while (characters.children.length > 1) {
      const character = characters.lastElementChild;
      if (character) {
        characters.removeChild(character);
      }
    }
    if (root.isObjectWithProperty(json, 'characters') && Array.isArray(json['characters'])) {
      for (const character of (json as { characters: {id: string, name: string}[] }).characters) {
        const characterElement = document.createElement('li');
        characterElement.setAttribute('class', 'name-edit-delete');
        characters.appendChild(characterElement);
        characterElement.appendChild(document.createElement('span'));
        characterElement.lastElementChild?.appendChild(document.createTextNode(character.name));
        characterElement.appendChild(root.button('[E]', 'Edit character', async (event: MouseEvent) => {
          event.stopPropagation();
          const el = document.createElement('textarea');
          el.setAttribute('id', 'character')
          const char = {...character} as {id?: string, name: string};
          delete char['id'];
          el.setAttribute('data-id', character.id);
          el.value = window?.jsyaml?.dump(char) ?? '';
          el.setAttribute('data-raw', el.value);
          document.body.appendChild(el);
        }));
        characterElement.appendChild(root.button('[D]', 'Delete character', async (event: MouseEvent) => {
          event.stopPropagation();
          if (await root.confirm("Do you want to delete this character sheet?")) {
            await root.getFromAPI(`chat/${chat.id}/characters/${character.id}/delete`, 'POST');
            await updateCharacters();
          }
        }));
      }
    }
  }
  sendButton.addEventListener('click', async function () {
    const value = chatEntry.value;
    if (!await root.maySendMessage() || !value || !value.trim()) {
      return;
    }
    chatEntry.value = '';
    const chatElement = document.createElement('li');
    chatWrapper.appendChild(chatElement);
    chatElement.innerHTML = purifier(converter.makeHtml(value));
    chatElement.classList.add('user');
    chatElement.scrollIntoView({ behavior: 'smooth' });
    const json = await root.getFromAPI(`chat/${chat.id}`, 'POST', {description: value}, 75000) as {message?: string, error?: string, exception?: string};
    if (typeof json === 'object' && Object.hasOwn(json, 'message')) {
      const message = (json as {message: string}).message;
      const reply = document.createElement('li');
      chatWrapper.appendChild(reply);
      reply.innerHTML = '<span class="gamemaster"></span>' + purifier(converter.makeHtml(message));
      reply.classList.add('agent');
      reply.scrollIntoView({ behavior: 'smooth' });
    }
  });
  let handlingClick = false;
  document.body.onclick = async (event) => {
    if (handlingClick) {
      return;
    }
    handlingClick = true;
    try {
      await root.uploadDocument(event, chat.id, 'character', async (element) => window?.jsyaml?.load(element.value) ?? {}, updateCharacters);
      await root.uploadDocument(event, chat.id, 'document', async (element) => {
        return {
          content: element.value,
          name: element.getAttribute('data-name') ?? await root.prompt("What is your document named?"),
        };
      }, updateDocuments);
    } finally {
      handlingClick = false;
    }
  }
  await updateCharacters();
  document.getElementById('add-character')?.addEventListener('click', async (event) => {
    event.stopPropagation();
    const el = document.createElement('textarea');
    el.setAttribute('id', 'character');
    el.value = characterFiller;
    document.body.appendChild(el);
  });
  await updateDocuments();
  document.getElementById('add-document')?.addEventListener('click', async (event) => {
    event.stopPropagation();
    const el = document.createElement('textarea');
    el.setAttribute('id', 'document');
    el.value = '';
    document.body.appendChild(el);
  });
  await (async () => {
    const json = await root.getFromAPI(`chat/${chat.id}`, 'GET');
    if (typeof json === 'object' && json !== null && Object.hasOwn(json, 'messages') && Array.isArray((json as {messages: []}).messages)) {
      for (const message of (json as {messages: {role: string, content: string}[]}).messages) {
        const listElement = document.createElement('li');
        chatWrapper.appendChild(listElement);
        const newHTML = converter.makeHtml(message.content);
        listElement.innerHTML = (message.role === 'agent' ? '<span class="gamemaster"></span>' : '') + purifier(newHTML);
        listElement.classList.add(message.role);
        listElement.scrollIntoView({ behavior: 'smooth' });
      }
      if (((json as {messages?: []})?.messages ?? [])?.length === 0 && !chatEntry.value && await root.confirm('Do you want help with your beginning scene? This will use up one of your messages.')) {
        const keywords = await root.prompt("What is the world like? Please provide keywords separated by comma.");
        world.value = keywords;
        world.dispatchEvent(new Event('change'));
        const selector = document.getElementById('music-select') as HTMLSelectElement|null;
        if (selector && await root.confirm('Do you want to turn on the background music?')) {
          selector.selectedIndex = 1;
          selector.dispatchEvent(new Event('change'));
        }
        if (await root.maySendMessage()) {
          const value = await root.getFromAPI(`chat/${chat.id}/starting-point-proposal`, 'POST', {
            name: await root.prompt("What is your character's name?"),
            heritage: await root.prompt("What is your character's heritage(race, species etc.)?"),
            gender: await root.selectFrom("What is your character's gender?", ['male', 'female', 'other', 'none']),
            wear: await root.prompt("What does your character wear?"),
            profession: await root.prompt("What is your character's profession?"),
            location: await root.prompt("Where is your character?"),
            purpose: await root.prompt("What is their purpose there?"),
            mood: await root.prompt("What is your character's mood?"),
            weather: await root.prompt("What is your weather like?"),
            genre: await root.prompt("What genre does the world fall into?"),
            world: keywords,
          });
          chatEntry.value = root.isObjectWithProperty(value, 'message') ? (value as { message: string })?.message : '';
          await updateCharacters();
          return;
        }
        await root.alert('You are currently out of messages, please wait a bit and try again by reloading the page.')
      }
    }
  })();
})(window.bjoernbuettner);
