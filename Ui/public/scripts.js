(async () => {
    const apiHost = location.protocol + '//' + location.hostname + '/api/v1'
    const characterFiller = await (await fetch('/char-template.yaml')).text();
    const chatId = (location.hash.replace(/[^0-9a-f-]+/g, '') || (await (await fetch(`${apiHost}/new`)).json()).chat);

    if (!chatId || !chatId.match(/^[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}$/i)) {
        window.location = location.protocol + '://' + location.host;
        return;
    }
    location.hash = `#${chatId}`;

    window.setInterval(async() => {
        try {
            const response = await fetch(
                `${apiHost}/chat/${chatId}/active`,
                {
                    signal: AbortSignal.timeout(100)
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
        } catch(e) {
            console.error(e);
        }
        document.getElementById('send').disabled = true;
        document.getElementById('loader').setAttribute('style', '');
    }, 1000);

    const updateCharacters = async () => {
        const response = await fetch(`${apiHost}/chat/${chatId}/characters`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
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
            while (document.getElementById('characters').children.length > 2) {
                document.getElementById('characters').removeChild(document.getElementById('characters').lastChild);
            }
            for (const character of json.characters) {
                document.getElementById('characters').appendChild(document.createElement('li'));
                document.getElementById('characters').lastChild.appendChild(document.createElement('span'));
                document.getElementById('characters').lastChild.lastChild.appendChild(document.createTextNode(character.name.taken));
                document.getElementById('characters').lastChild.appendChild(document.createElement('span'));
                document.getElementById('characters').lastChild.lastChild.appendChild(document.createTextNode('[E]'));
                document.getElementById('characters').lastChild.lastChild.classList.add('button');
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
                document.getElementById('characters').lastChild.lastChild.onclick = async (event) => {
                    event.stopPropagation();
                    if (confirm("Do you want to delete this character sheet?")) {
                        await fetch(`${apiHost}/chat/${chatId}/characters/${character._id['$oid']}`, {
                            method: 'DELETE'
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
            const response = await fetch(`${apiHost}/chat/${chatId}`, {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({description: value}),
                credentials: "include"
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
    await (async() => {
        const response = await fetch(`${apiHost}/chat/${chatId}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            credentials: "include"
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
                if (confirm("Do you want to save this character sheet?")) {
                    if (el.hasAttribute('data-id')) {
                        if (el.value && el.getAttribute('data-raw') !== el.value) {
                            const id = el.getAttribute('data-id');
                            await fetch(`${apiHost}/chat/${chatId}/characters/${id}`, {
                                method: 'PUT',
                                headers: {
                                    'Accept': 'application/json',
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify(jsyaml.load(el.value)),
                                credentials: "include"
                            });
                        }
                    } else if(el.value) {
                        await fetch(`${apiHost}/chat/${chatId}/characters`, {
                            method: 'POST',
                            headers: {
                                'Accept': 'application/json',
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(jsyaml.load(el.value)),
                            credentials: "include"
                        })
                    }
                }
                document.body.removeChild(el);
                await updateCharacters();
            }
        }
    }
    await updateCharacters();
    document.getElementById('add-character').onclick = async(event) => {
        event.stopPropagation();
        const el = document.createElement('textarea');
        el.setAttribute('id', 'charactersheet');
        el.value = characterFiller;
        document.body.appendChild(el);
    }
    await (async() => {
        const response = await fetch(`${apiHost}/chat/${chatId}/world`, {
            method: "GET",
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            credentials: "include"
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
        fetch(`${apiHost}/chat/${chatId}/world`, {
            method: "PUT",
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                keywords
            })
        })
    }
    if (window.matchMedia && !window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.getElementsByTagName('html')[0]?.classList.toggle('inverted-colors');
    }
    document.getElementById('logo').onclick = () => {
        document.getElementsByTagName('html')[0]?.classList.toggle('inverted-colors');
    }
})();