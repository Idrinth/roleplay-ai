const chatId = '398a21e2-34a1-43b0-b524-5341cf55e060';

(async () => {
    document.getElementById('send').addEventListener('click', async function () {
        const now = Date.now();
        const value = document.getElementById('chat-entry').value;
        if (!value) {
            return;
        }
        document.getElementById('send').disabled = true;
        document.getElementById('chat-entry').value = '';
        document.getElementById('chat').appendChild(document.createElement('li'));
        document.getElementById('chat').lastChild.appendChild(document.createTextNode(value));
        document.getElementById('chat').lastChild.classList.add('user');
        document.getElementById('chat').appendChild(document.createElement('li'));
        document.getElementById('chat').lastChild.appendChild(document.createElement('img'));
        document.getElementById('chat').lastChild.lastChild.setAttribute('src', '/loader.gif')
        try {
            const response = await fetch(`http://localhost:8000/chat/${chatId}`, {
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
                    document.getElementsByTagName('ul')[0].appendChild(document.createElement('li'));
                    document.getElementsByTagName('ul')[0].lastChild.appendChild(document.createTextNode(json.message));
                    document.getElementsByTagName('ul')[0].lastChild.classList.add('agent');
                }
            }
        } catch(e) {
            console.error(e);
        }
        document.getElementById('send').disabled = false;
        document.getElementsByTagName('img')[1].parentNode.parentNode.removeChild(
            document.getElementsByTagName('img')[1].parentNode
        );
        console.log(`Reply took ${Date.now() / 1000 - now / 1000}s`);
    });
    const response = await fetch(`http://localhost:8000/chat/${chatId}`, {
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
            for (const message of json.messages) {
                document.getElementById('chat').appendChild(document.createElement('li'));
                document.getElementById('chat').lastChild.appendChild(document.createTextNode(message.content));
                document.getElementById('chat').lastChild.classList.add(message.role);
            }
        }
    }
})();
(async() => {
    document.body.onclick = (event) => {
        const el = document.getElementsByTagName('pre');
        if (el && el.length > 0) {
            if (event.target !== el[0]) {
                document.body.removeChild(el[0]);
            }
        }
    }
    const response = await fetch(`http://localhost:8000/chat/${chatId}/characters`, {
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
            for (const character of json.characters) {
                document.getElementById('characters').appendChild(document.createElement('li'));
                document.getElementById('characters').lastChild.appendChild(document.createTextNode(character.name.taken));
                document.getElementById('characters').lastChild.onclick = (event) => {
                    event.stopPropagation();
                    const el = document.createElement('pre');
                    const char = {...character};
                    char._id = undefined;
                    el.appendChild(document.createTextNode(jsyaml.dump(char)));
                    document.body.appendChild(el);
                }
            }
        }
    }
})()