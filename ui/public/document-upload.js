(async(root) => {
  root.uploadDocument = async(event, chatId, resource, getBody, updateFunction) => {
    const element = document.getElementById(resource);
    if (!element) {
      return;
    }
    if (event.target === element) {
      return;
    }
    const upload = async() => {
      const id = element.getAttribute('data-id');
      if (id && element.value && element.getAttribute('data-raw') !== element.value && await root.confirm("Do you want to save this modified character sheet?")) {
        await root.getFromAPI(`chat/${chatId}/${resource}/${id}`, JSON.stringify(getBody(element)));
        return;
      }
      if (element.value && await root.confirm("Do you want to save this new character sheet?")) {
        await root.getFromAPI(`chat/${chatId}/${resource}`, 'POST', JSON.stringify(getBody(element)));
      }
    }
    await upload();
    document.body.removeChild(element);
    await updateFunction();
  }
})(window.bjoernbuettner);
