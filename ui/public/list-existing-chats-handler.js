window.bjoernbuettner = window.bjoernbuettner || {};
((addTo) => {
  addTo.listExistingChats = (chats, chatId = null) => {
    const worlds = document.getElementById('worlds');
    for (const achat of chats) {
      worlds.appendChild(document.createElement('li'));
      const world = document.getElementById('worlds').lastElementChild;
      world.appendChild(document.createElement('a'));
      world.lastElementChild.innerHTML = achat.name;
      world.lastElementChild.setAttribute('href', '/chat/' + achat.id);
      world.lastElementChild.setAttribute('data-id', achat.id);
      world.appendChild(bjoernbuettner.button('[E]', 'Change chat name', async () => {
        const name = await bjoernbuettner.prompt(`What is the new name for ${achat.name}?`, achat.name);
        achat.name = name;
        await fetch(
          `${bjoernbuettner.apiEndpoint}/chat/${achat.id}/name`,
          {
            credentials: "include",
            method: "POST",
            signal: AbortSignal.timeout(10000),
            body: JSON.stringify({
              name,
            })
          }
        );
      }));
      world.appendChild(bjoernbuettner.button('[D]', 'Delete chat', async () => {
        if (await bjoernbuettner.confirm(`Do you want to delete ${achat.name}?`)) {
          await fetch(
            `${bjoernbuettner.apiEndpoint}/chat/${achat.id}/delete`,
            {
              credentials: "include",
              method: "POST",
              signal: AbortSignal.timeout(10000),
            }
          );
          if (chatId === achat.id) {
            window.location = location.protocol + '//' + location.host + '/chat';
            return;
          }
          document.getElementById('worlds').removeChild(world);
        }
      }));
    }
  }
})(window.bjoernbuettner);
