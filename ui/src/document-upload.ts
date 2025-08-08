(async(root) => {
  root.uploadDocument = async(event: Event, chatId: string, resource: string, getBody: (element: HTMLTextAreaElement) => Promise<any>, updateFunction: () => Promise<void>): Promise<void> => {
    const element = document.getElementById(resource) as HTMLTextAreaElement|null;
    if (!element || element.tagName !== 'TEXTAREA') {
      return;
    }
    if (event.target === element) {
      return;
    }
    const upload = async() => {
      const id = element.getAttribute('data-id');
      if (id && element.value && element.getAttribute('data-raw') !== element.value && await root.confirm(`Do you want to save this modified ${resource}?`)) {
        return await root.getFromAPI(`chat/${chatId}/${resource}s/${id}`, 'POST', await getBody(element));
      }
      if (element.value && await root.confirm(`Do you want to save this new ${resource}?`)) {
        return await root.getFromAPI(`chat/${chatId}/${resource}s`, 'POST', await getBody(element));
      }
      return undefined;
    }
    await upload();
    element.parentElement?.removeChild(element);
    await updateFunction();
  }
})(window.bjoernbuettner);
