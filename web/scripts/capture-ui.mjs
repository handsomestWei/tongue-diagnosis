/**
 * 启动 vite preview 后对各路由截全页图，输出到 docs/ui-screenshots/
 * 用法：先在 web 目录 npm run build，再 node scripts/capture-ui.mjs
 * 或：npm run capture-ui（会先试构建）
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

const baseURL = 'http://127.0.0.1:4173'
const routes = [
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

async function waitForServer(url, maxMs = 90_000) {
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

async function main() {
  fs.mkdirSync(outDir, { recursive: true })

  const child = spawn('npx', ['vite', 'preview', '--host', '127.0.0.1', '--port', '4173', '--strictPort'], {
    cwd: webRoot,
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env },
  })

  let stderr = ''
  child.stderr?.on('data', (d) => {
    stderr += d.toString()
  })

  try {
    await waitForServer(`${baseURL}/`)
    const browser = await chromium.launch({ headless: true })
    const page = await browser.newPage({
      viewport: { width: 1440, height: 900 },
    })

    for (const [fileBase, routePath] of routes) {
      const url = `${baseURL}${routePath}`
      await page.goto(url, { waitUntil: 'domcontentloaded' })
      await sleep(500)
      const outPath = path.join(outDir, `${fileBase}.png`)
      await page.screenshot({ path: outPath, fullPage: true })
      console.log('saved', path.relative(repoRoot, outPath))
    }

    await browser.close()
  } catch (e) {
    console.error(stderr)
    throw e
  } finally {
    child.kill('SIGTERM')
    await sleep(400)
  }
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
