import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

/** Read the repo-root .env. The dev server needs the password because a 401 on
 *  fetch() does not make the browser prompt the way a navigation does — without
 *  this, setting a password to share the app breaks local development. The
 *  header is added by the proxy, server-side; it never reaches client code. */
function authHeader(): Record<string, string> {
  try {
    const env = readFileSync(resolve(__dirname, '..', '.env'), 'utf8')
    const get = (k: string) => env.match(new RegExp(`^${k}=(.*)$`, 'm'))?.[1]?.trim()
    const password = get('LL_TEXTREADER_PASSWORD')
    if (!password) return {}
    const user = get('LL_TEXTREADER_USERNAME') || 'read'
    return { Authorization: 'Basic ' + Buffer.from(`${user}:${password}`).toString('base64') }
  } catch {
    return {}
  }
}

export default defineConfig({
  plugins: [react()],
  server: {
    // the FastAPI backend; keeps the frontend same-origin in dev
    proxy: { '/api': { target: 'http://127.0.0.1:8000', headers: authHeader() } },
  },
})
