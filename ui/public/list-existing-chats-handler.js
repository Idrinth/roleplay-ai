((root) => {
  root.listExistingChats = (chats, chatId = null) => {
    const worlds = document.getElementById('worlds');
    for (const achat of chats) {
      worlds.appendChild(document.createElement('li'));
      const world = document.getElementById('worlds').lastElementChild;
      world.appendChild(document.createElement('a'));
      world.lastElementChild.innerText = achat.name;
      world.lastElementChild.setAttribute('href', '/chat/' + achat.id);
      world.lastElementChild.setAttribute('data-id', achat.id);
      world.appendChild(root.button('[E]', 'Change chat name', async () => {
        const name = await root.prompt(`What is the new name for ${achat.name}?`, achat.name);
        achat.name = name;
        await root.getFromAPI(
          `chat/${achat.id}/name`,
          'POST',
          {name}
        );
        world.lastElementChild.innerText = name;
      }));
      world.appendChild(root.button('[D]', 'Delete chat', async () => {
        if (await root.confirm(`Do you want to delete ${achat.name}?`)) {
          await root.getFromAPI(
            `chat/${achat.id}/delete`,
            'POST',
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
