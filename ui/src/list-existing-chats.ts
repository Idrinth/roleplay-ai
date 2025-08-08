(async(root) => {
  const user = await (async () => {
    const user = await root.getFromAPI(`whoami`, 'GET');
    if (!user?.error && !user?.exception) {
      return user;
    }
    return undefined;
  })() as undefined|{id: string,chats:{id:string, name: string}[]};
  if (!user) {
    return;
  }
  root.listExistingChats(user.chats)
})(window.bjoernbuettner);
