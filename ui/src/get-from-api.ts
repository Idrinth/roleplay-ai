((root) => {
  root.getFromAPI = async(endpoint: string, method: 'POST'|'GET'|'PUT', body: object|undefined = undefined, timeout: number = 600000, decode: boolean = true): Promise<unknown> => {
    try {
      const content = await fetch(`${window.location.protocol}//###DESIRED_ROOT###/api/v1/${endpoint}`, {
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
        },
        signal: AbortSignal.timeout(timeout),
        body: body ? JSON.stringify(body) : null,
        method,
      });
      return await (decode? content.json() : content.text());
    } catch (e) {
      return {exception: `${e}`};
    }
  }
})(window.bjoernbuettner)
