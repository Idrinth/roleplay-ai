((root) => {
  root.getFromAPI = async(endpoint: string, method: 'POST'|'GET'|'PUT', body: any = undefined, timeout: number = 600000, decode: boolean = true): Promise<unknown> => {
    try {
      const content = await fetch(`/api/v1/${endpoint}`, {
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
