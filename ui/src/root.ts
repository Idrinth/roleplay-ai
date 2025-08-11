declare global {
  interface Window {
    bjoernbuettner: {
      audios: {src: string, keyword: string}[],
      isObjectWithProperty: <K extends PropertyKey>(value: unknown, key: string) => value is object & Record<K, unknown>,
      button: (text: string, title: string, callback: (ev: MouseEvent) => void, useActualButton: boolean) => HTMLButtonElement|HTMLSpanElement,
      alert: (text: string) => Promise<void>,
      confirm: (text: string) => Promise<boolean>,
      password: (minChars: number, maxChar: number) => string,
      prompt: (text: string, defaultText: string) => Promise<string>,
      listExistingChats: (chats: {id: string, name: string}[], chatId: string) => void,
      getFromAPI: (endpoint: string, method: 'POST'|'GET'|'PUT', body: object, timeout: number, decode: boolean) => Promise<unknown|{exception: string}>,
      uploadDocument: (event: Event, chatId: string, resource: string, getBody: (element: HTMLTextAreaElement) => Promise<object>, updateFunction: () => Promise<void>) => Promise<void>,
    } & {
      button: (text: string, title: string, callback: (ev: MouseEvent) => void) => HTMLButtonElement|HTMLSpanElement,
      prompt: (text: string) => Promise<string>,
      password: (minChars: number) => string,
      listExistingChats: (chats: {id: string, name: string}[]) => void,
      getFromAPI: (endpoint: string, method: 'POST'|'GET'|'PUT', body: object|undefined, timeout: number) => Promise<unknown|{exception: string}>,
    } & {
      password: () => string,
      getFromAPI: (endpoint: string, method: 'POST'|'GET'|'PUT', body: object|undefined) => Promise<unknown|{exception: string}>,
    } & {
      getFromAPI: (endpoint: string, method: 'POST'|'GET'|'PUT') => Promise<unknown|{exception: string}>,
    },
    jsyaml?: {
      load: <T = unknown>(input: string) => T,
      dump: (input: object) => string,
    },
    showdown?: {
      Converter: new () => {
        makeHtml: (content: string) => string,
      },
    },
    DOMPurify?: {
      sanitize: (html: string) => string,
    }
  }
}

window.bjoernbuettner = window.bjoernbuettner || {};
