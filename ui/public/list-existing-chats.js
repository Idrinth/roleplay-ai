(async() => {
  const user = await (async () => {
    const user = await (await fetch(`${bjoernbuettner.apiEndpoint}/whoami`, {
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
  bjoernbuettner.listExistingChats(user.chats)
})();
