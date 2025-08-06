((root) => {
  root.getFromAPI = async(endpoint, method, body = null, timeout = 600000, decode = true) => {
    try {
      const content = await fetch(`${root.apiEndpoint}/${endpoint}`, {
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
        },
        signal: AbortSignal.timeout(timeout),
        body: body ? JSON.stringify(body) : undefined,
        method,
      });
      return await (decode? content.json() : content.text());
    } catch (e) {
      return {exception: `${e}`};
    }
  }
})(window.bjoernbuettner)
