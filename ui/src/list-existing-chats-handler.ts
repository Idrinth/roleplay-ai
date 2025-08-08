((root) => {
  root.listExistingChats = (chats: {id: string, name: string}[], chatId: string|undefined = undefined): void => {
    const worlds = document.getElementById('worlds');
    if (!worlds) {
      return;
    }
    for (const achat of chats) {
      worlds.appendChild(document.createElement('li'));
      const world = document.getElementById('worlds')?.lastElementChild;
      if (!world) {
        continue;
      }
      const link = document.createElement('a');
      world.appendChild(link);
      link.innerText = achat.name;
      link.setAttribute('href', '/chat/' + achat.id);
      link.setAttribute('data-id', achat.id);
      world.appendChild(root.button('[E]', 'Change chat name', async () => {
        const name = await root.prompt(`What is the new name for ${achat.name}?`, achat.name);
        achat.name = name;
        await root.getFromAPI(
          `chat/${achat.id}/name`,
          'POST',
          {name}
        );
        link.innerText = name;
      }));
      world.appendChild(root.button('[D]', 'Delete chat', async () => {
        if (await root.confirm(`Do you want to delete ${achat.name}?`)) {
          await root.getFromAPI(
            `chat/${achat.id}/delete`,
            'POST',
          );
          if (chatId === achat.id) {
            window.location.assign(location.protocol + '//' + location.host + '/chat');
            return;
          }
          worlds.removeChild(world);
        }
      }));
    }
  }
})(window.bjoernbuettner);
