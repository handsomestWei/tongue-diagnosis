/**
 * 启动 FastAPI + vite preview，以 admin 登录后对各路由截全页图 → docs/ui-screenshots/
 * 需仓库根目录存在 .venv 且已 pip install -e ".[api]"
 */
import { chromium } from 'playwright'
import { spawn } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const webRoot = path.resolve(__dirname, '..')
const repoRoot = path.resolve(webRoot, '..')
const outDir = path.join(repoRoot, 'docs', 'ui-screenshots')

const webBase = 'http://127.0.0.1:4173'
const apiBase = 'http://127.0.0.1:8000'

const routes = [
  ['00-login', '/login'],
  ['01-dashboard', '/'],
  ['02-upload', '/upload'],
  ['03-annotate', '/annotate'],
  ['04-train', '/train'],
  ['05-train-incremental', '/train/incremental'],
  ['06-infer', '/infer'],
  ['07-review', '/review'],
  ['08-models', '/models'],
  ['09-settings', '/settings'],
]

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms))
}

async function waitForUrl(url, maxMs = 90_000) {
  const start = Date.now()
  while (Date.now() - start < maxMs) {
    try {
      const res = await fetch(url, { method: 'GET' })
      if (res.ok) return
    } catch {
      /* retry */
    }
    await sleep(250)
  }
  throw new Error(`Server not ready: ${url}`)
}

function pickPython() {
  const venvPy = path.join(repoRoot, '.venv', 'bin', 'python')
  if (fs.existsSync(venvPy)) return venvPy
  return 'python3'
}

async function loginAdminSession() {
  const body = new URLSearchParams({ username: 'admin', password: 'admin123' })
  const res = await fetch(`${apiBase}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })
  if (!res.ok) {
    const t = await res.text()
    throw new Error(`Login failed ${res.status}: ${t}`)
  }
  return res.json()
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true })

  const py = pickPython()
  const apiChild = spawn(py, ['-m', 'uvicorn', 'api.main:app', '--host', '127.0.0.1', '--port', '8000'], {
    cwd: repoRoot,
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env, PYTHONPATH: repoRoot },
  })

  const webChild = spawn('npx', ['vite', 'preview', '--host', '127.0.0.1', '--port', '4173', '--strictPort'], {
    cwd: webRoot,
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env },
  })

  let apiErr = ''
  let webErr = ''
  apiChild.stderr?.on('data', (d) => {
    apiErr += d.toString()
  })
  webChild.stderr?.on('data', (d) => {
    webErr += d.toString()
  })

  try {
    await waitForUrl(`${apiBase}/health`)
    await waitForUrl(`${webBase}/`)

    const auth = await loginAdminSession()

    const browser = await chromium.launch({ headless: true })
    const context = await browser.newContext({
      viewport: { width: 1440, height: 900 },
    })

    await context.addInitScript(
      ({ token, username, full_name, role }) => {
        localStorage.setItem('td_access_token', token)
        localStorage.setItem(
          'td_user',
          JSON.stringify({ username, full_name, role }),
        )
      },
      {
        token: auth.access_token,
        username: auth.username,
        full_name: auth.full_name,
        role: auth.role,
      },
    )

    const pageNoAuth = await browser.newPage({ viewport: { width: 1440, height: 900 } })
    await pageNoAuth.goto(`${webBase}/login`, { waitUntil: 'domcontentloaded' })
    await sleep(500)
    await pageNoAuth.screenshot({ path: path.join(outDir, '00-login.png'), fullPage: true })
    console.log('saved', path.relative(repoRoot, path.join(outDir, '00-login.png')))
    await pageNoAuth.close()

    const page = await context.newPage()

    for (const [fileBase, routePath] of routes) {
      if (fileBase === '00-login') continue
      const url = `${webBase}${routePath}`
      await page.goto(url, { waitUntil: 'domcontentloaded' })
      await sleep(500)
      const outPath = path.join(outDir, `${fileBase}.png`)
      await page.screenshot({ path: outPath, fullPage: true })
      console.log('saved', path.relative(repoRoot, outPath))
    }

    await browser.close()
  } catch (e) {
    console.error(apiErr)
    console.error(webErr)
    throw e
  } finally {
    apiChild.kill('SIGTERM')
    webChild.kill('SIGTERM')
    await sleep(500)
  }
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
