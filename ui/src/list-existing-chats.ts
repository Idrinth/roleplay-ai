(async(root) => {
  const user = await root.getUser();
  if (!user) {
    return;
  }
  root.listExistingChats(user.chats)
})(window.bjoernbuettner);
