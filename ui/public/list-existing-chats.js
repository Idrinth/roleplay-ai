(async() => {
  const apiHost = '/api/v1';

  const user = await (async () => {
    const user = await (await fetch(`${apiHost}/whoami`, {
      credentials: "include",
      method: "GET",
    })).json();
    if (!user.error && !user.exception) {
      return user;
    }
    return undefined;
  })();
  if (!user) {
    return;
  }
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
    world.lastElementChild.onclick = async () => {
      if (await bjoernbuettner.confirm(`Do you want to delete ${achat.name}?`)) {
        await fetch(
          `${apiHost}/chat/${achat.id}/delete`,
          {
            credentials: "include",
            method: "POST",
            signal: AbortSignal.timeout(10000),
          }
        );
        document.getElementById('worlds').removeChild(world);
      }
    }
  }
})();
