(async () => {
    const apiHost = location.protocol + '//' + location.hostname + ':8000'

    const chatId = (location.hash.replace(/[^0-9a-f-]+/g, '') || (await (await fetch(`${apiHost}/new`)).json()).chat);

    if (!chatId || !chatId.match(/^[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}$/i)) {
        window.location = location.protocol + '://' + location.host + ':8080';
        return;
    }
    location.hash = `#${chatId}`;
    const updateCharacters = async () => {
        const response = await fetch(`${apiHost}/chat/${chatId}/characters`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        if (response.ok) {
            const json = await response.json();
            if (json.error) {
                console.error(json.error);
            } else if (json.exception) {
                console.error(json.exception);
            } else {
                while (document.getElementById('characters').children.length > 1) {
                    document.getElementById('characters').removeChild(document.getElementById('characters').lastChild);
                }
                for (const character of json.characters) {
                    document.getElementById('characters').appendChild(document.createElement('li'));
                    document.getElementById('characters').lastChild.appendChild(document.createTextNode(character.name.taken));
                    document.getElementById('characters').lastChild.onclick = (event) => {
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
                }
            }
        }
    };
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
        document.getElementById('chat').appendChild(document.createElement('li'));
        document.getElementById('chat').lastChild.appendChild(document.createElement('img'));
        document.getElementById('chat').lastChild.lastChild.setAttribute('src', '/loader.gif');
        document.getElementById('chat').lastChild.lastChild.setAttribute('id', 'loader');
        try {
            const response = await fetch(`${apiHost}/chat/${chatId}`, {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({description: value}),
            });
            if (response.ok) {
                const json = await response.json();
                if (json.error) {
                    console.error(json.error);
                } else if (json.exception) {
                    console.error(json.exception);
                } else {
                    document.getElementById('chat').appendChild(document.createElement('li'));
                    document.getElementById('chat').lastChild.innerHTML = converter.makeHtml(json.message);
                    document.getElementById('chat').lastChild.classList.add('agent');
                }
            }
        } catch (e) {
            console.error(e);
        }
        document.getElementById('send').disabled = false;
        document.getElementById('loader').parentNode.parentNode.removeChild(
            document.getElementById('loader').parentNode
        );
        console.log(`Reply took ${Date.now() / 1000 - now / 1000}s`);
    });
    const response = await fetch(`${apiHost}/chat/${chatId}`, {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
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
                document.getElementById('chat').lastChild.innerHTML = converter.makeHtml(message.content);
                document.getElementById('chat').lastChild.classList.add(message.role);
            }
        }
    }
    document.body.onclick = async (event) => {
        const el = document.getElementById('charactersheet');
        if (el) {
            if (event.target !== el) {
                if (el.hasAttribute('data-id')) {
                    if (el.getAttribute('data-raw') !== el.value) {
                        const id = el.getAttribute('data-id');
                        await fetch(`${apiHost}/chat/${chatId}/characters/${id}`, {
                            method: 'PUT',
                            headers: {
                                'Accept': 'application/json',
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(jsyaml.load(el.value))
                        });
                    }
                } else {
                    await fetch(`${apiHost}/chat/${chatId}/characters`, {
                        method: 'POST',
                        headers: {
                            'Accept': 'application/json',
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(jsyaml.load(el.value))
                    })
                }
                document.body.removeChild(el);
                await updateCharacters();
            }
        }
    }
    await updateCharacters();
    document.getElementById('add-character').onclick = (event) => {
        event.stopPropagation();
        const el = document.createElement('textarea');
        el.setAttribute('id', 'charactersheet');
        document.body.appendChild(el);
    }
})();