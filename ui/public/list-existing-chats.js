(async(root) => {
  const user = await (async () => {
    const user = root.getFromAPI(`whoami`, 'GET');
    if (!user.error && !user.exception) {
      return user;
    }
    return undefined;
  })();
  if (!user) {
    return;
  }
  root.listExistingChats(user.chats)
})(window.bjoernbuettner);
