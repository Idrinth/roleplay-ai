(async () => {
    const chatId = '398a21e2-34a1-43b0-b524-5341cf55e060';

    document.getElementsByTagName('button')[0].addEventListener('click', async function () {
        const now = Date.now();
        const value = document.getElementsByTagName('textarea')[0].value;
        if (!value) {
            return;
        }
        document.getElementsByTagName('button')[0].disabled = true;
        document.getElementsByTagName('textarea')[0].value = '';
        document.getElementsByTagName('ul')[0].appendChild(document.createElement('li'));
        document.getElementsByTagName('ul')[0].lastChild.appendChild(document.createTextNode(value));
        document.getElementsByTagName('ul')[0].lastChild.classList.add('user');
        document.getElementsByTagName('ul')[0].appendChild(document.createElement('img'));
        document.getElementsByTagName('ul')[0].lastChild.setAttribute('src', '/loader.gif')
        const response = await fetch(`http://localhost:8000/chat/${chatId}`, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({description: value}),
            signal: AbortSignal.timeout(3600000),
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
        document.getElementsByTagName('button')[0].disabled = false;
        document.getElementsByTagName('img')[0].parentNode.removeChild(document.getElementsByTagName('img')[0]);
        console.log(`Reply took ${Date.now() / 1000 - now / 1000}s`);
    });
    const response = await fetch(`http://localhost:8000/chat/${chatId}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            signal: AbortSignal.timeout(3600000),
    });
    if (response.ok) {
        const json = await response.json();
        if (json.error) {
            console.error(json.error);
        } else if (json.exception) {
            console.error(json.exception);
        } else {
            for (const message of json.messages) {
                document.getElementsByTagName('ul')[0].appendChild(document.createElement('li'));
                document.getElementsByTagName('ul')[0].lastChild.appendChild(document.createTextNode(message.content));
                document.getElementsByTagName('ul')[0].lastChild.classList.add(message.role);
            }
        }
    }
})();