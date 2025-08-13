(async(root) => {
  let ready = false;
  const user = await (async () => {
    const user = await root.getFromAPI(`whoami`, 'GET');
    if (typeof user !== 'object' || user === null) {
      return undefined;
    }
    if (!Object.hasOwn(user, 'error') && !Object.hasOwn(user, 'exception')) {
      return user;
    }
    return undefined;
  })() as undefined | { id: string, name?: string, chats: { id: string, name: string }[] };
  ready = true;
  root.getUser = async()  => {
    while (!ready) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    return user;
  }
})(window.bjoernbuettner)
