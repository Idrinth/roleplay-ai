(async(root) => {
  if (!root.user) {
    return;
  }
  root.listExistingChats(root.user.chats)
})(window.bjoernbuettner);
