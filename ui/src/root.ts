declare global {
  interface Window {
    bjoernbuettner: {
      button: (text: string, title: string, callback: (ev: MouseEvent) => void, useActualButton: boolean) => HTMLButtonElement|HTMLSpanElement,
      alert: (text: string) => Promise<void>,
      confirm: (text: string) => Promise<boolean>,
      prompt: (text: string, defaultText: string) => Promise<string>,
      listExistingChats: (chats: {id: string, name: string}[], chatId: string) => void,
      getFromAPI: (endpoint: string, method: 'POST'|'GET'|'PUT', body: object, timeout: number, decode: boolean) => Promise<unknown|{exception: string}>,
      uploadDocument: (event: Event, chatId: string, resource: string, getBody: (element: HTMLTextAreaElement) => Promise<object>, updateFunction: () => Promise<void>) => Promise<void>,
    } & {
      button: (text: string, title: string, callback: (ev: MouseEvent) => void) => HTMLButtonElement|HTMLSpanElement,
      prompt: (text: string) => Promise<string>,
      listExistingChats: (chats: {id: string, name: string}[]) => void,
      getFromAPI: (endpoint: string, method: 'POST'|'GET'|'PUT', body: object, timeout: number) => Promise<unknown|{exception: string}>,
    } & {
      getFromAPI: (endpoint: string, method: 'POST'|'GET'|'PUT', body: object) => Promise<unknown|{exception: string}>,
    } & {
      getFromAPI: (endpoint: string, method: 'POST'|'GET'|'PUT') => Promise<unknown|{exception: string}>,
    },
    PayPal?: {
      Donation?: {
        Button?: (config: {
          env: 'production'
          hosted_button_id: string,
          image: {
            src: string,
            alt: string,
            title: string,
          },
        }) => {render: (id: string) => HTMLElement},
      },
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
  }
}

window.bjoernbuettner = window.bjoernbuettner || {};
