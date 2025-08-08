declare global {
  interface Window {
    bjoernbuettner: {
      apiEndpoint: string,
      button: (text: string, title: string, callback: (ev: MouseEvent) => void, useActualButton: boolean) => HTMLButtonElement|HTMLSpanElement,
      alert: (text: string) => Promise<void>,
      confirm: (text: string) => Promise<boolean>,
      prompt: (text: string, defaultText: string) => Promise<string>,
      listExistingChats: (chats: {id: string, name: string}[], chatId: string) => void,
      getFromAPI: (endpoint: string, method: 'POST'|'GET'|'PUT', body: any, timeout: number, decode: boolean) => Promise<{}|{exception: string}>,
      uploadDocument: (event: Event, chatId: string, resource: string, getBody: (element: HTMLTextAreaElement) => any, updateFunction: Function) => Promise<void>,
    } & {
      button: (text: string, title: string, callback: (ev: MouseEvent) => void) => HTMLButtonElement,
      prompt: (text: string) => Promise<string>,
      listExistingChats: (chats: {id: string, name: string}[]) => void,
      getFromAPI: (endpoint: string, method: 'POST'|'GET'|'PUT', body: any, timeout: number) => Promise<object|{exception: string}>,
    } & {
      getFromAPI: (endpoint: string, method: 'POST'|'GET'|'PUT', body: any) => Promise<object|{exception: string}>,
    } & {
      getFromAPI: (endpoint: string, method: 'POST'|'GET'|'PUT') => Promise<object|{exception: string}>,
    },
    PayPal: {
      Donation: {
        Button: (config: {}) => {render: (id: string) => HTMLElement},
      },
    },
    jsyaml: {
      load: (input: string) => {},
      dump: (input: any) => string,
    },
    showdown: {
      Converter: new () => {
        makeHtml: (content: string) => HTMLElement,
      },
    },
  }
}

window.bjoernbuettner = window.bjoernbuettner || {};
