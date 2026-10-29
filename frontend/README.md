# frontend

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Recommended Browser Setup

- Chromium-based browsers (Chrome, Edge, Brave, etc.):
  - [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd)
  - [Turn on Custom Object Formatter in Chrome DevTools](http://bit.ly/object-formatters)
- Firefox:
  - [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
  - [Turn on Custom Object Formatter in Firefox DevTools](https://fxdx.dev/firefox-devtools-custom-object-formatters/)

## Type Support for `.vue` Imports in TS

TypeScript cannot handle type information for `.vue` imports by default, so we replace the `tsc` CLI with `vue-tsc` for type checking. In editors, we need [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) to make the TypeScript language service aware of `.vue` types.

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

The frontend proxies `/api/chat` to `http://127.0.0.1:8000/chat` during
development. Start the FastAPI backend on port 8000 before sending chat messages.

If the frontend runs in WSL and the backend runs on Windows, set the proxy target
to the Windows host gateway address before starting Vite:

```sh
export VITE_BACKEND_TARGET="http://$(ip route show | awk '/default/ {print $3; exit}'):8000"
npm run dev
```

In this setup, start the Windows backend listening on all interfaces, for example
with `uvicorn main:app --reload --host 0.0.0.0`. Allow port 8000 through Windows
Firewall only for the local/WSL network as appropriate. Restart both servers
after changing these settings.

### Type-Check, Compile and Minify for Production

```sh
npm run build
```
