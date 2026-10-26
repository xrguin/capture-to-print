import test from 'node:test'
import assert from 'node:assert/strict'
import { existsSync, lstatSync, mkdirSync, mkdtempSync, readlinkSync, rmSync, symlinkSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

const sandbox = mkdtempSync(path.join(tmpdir(), 'capture-to-print-link-'))
process.env.DSH_HOME = path.join(sandbox, 'dsh')
process.env.CAPTURE_TO_PRINT_HOME = path.join(sandbox, 'data')

const { apply } = await import('../lib/index.mjs')
const packageRoot = path.resolve(import.meta.dirname, '..')
const skillTarget = path.join(packageRoot, 'skills', 'capture-to-print')
const skillLink = path.join(process.env.DSH_HOME, 'skills', 'capture-to-print')
const appLink = path.join(process.env.CAPTURE_TO_PRINT_HOME, 'app')

function context() {
  const handlers = new Map()
  return {
    logger: { info() {} },
    on(event, handler) {
      handlers.set(event, handler)
    },
    dispose() {
      handlers.get('dispose')?.()
    },
  }
}

test('links the bundled skill and app path', () => {
  const ctx = context()
  apply(ctx, {})
  assert.equal(readlinkSync(skillLink), skillTarget)
  assert.equal(readlinkSync(appLink), packageRoot)
  assert.ok(existsSync(path.join(skillLink, 'SKILL.md')))
  assert.ok(existsSync(path.join(appLink, 'scripts', 'capture_to_print.py')))
  ctx.dispose()
  assert.equal(existsSync(skillLink), false)
  assert.equal(existsSync(appLink), false)
})

test('re-applying is idempotent', () => {
  const ctx = context()
  apply(ctx, {})
  const before = readlinkSync(skillLink)
  apply(context(), {})
  assert.equal(readlinkSync(skillLink), before)
  ctx.dispose()
})

test('refuses to replace a foreign link or directory', () => {
  const foreign = path.join(sandbox, 'foreign-skill')
  mkdirSync(foreign, { recursive: true })
  mkdirSync(path.dirname(skillLink), { recursive: true })
  symlinkSync(foreign, skillLink, 'dir')

  const ctx = context()
  apply(ctx, {})
  assert.equal(readlinkSync(skillLink), foreign)
  ctx.dispose()
  assert.equal(readlinkSync(skillLink), foreign)
  assert.equal(existsSync(foreign), true)

  rmSync(skillLink)
  mkdirSync(skillLink, { recursive: true })
  apply(context(), {})
  assert.equal(lstatSync(skillLink).isDirectory(), true)
  rmSync(skillLink, { recursive: true })
})

test('honours explicit roots', () => {
  const skills = path.join(sandbox, 'custom-skills')
  const app = path.join(sandbox, 'custom-app')
  apply(context(), { skillsRoot: skills, appLink: app })
  assert.equal(readlinkSync(path.join(skills, 'capture-to-print')), skillTarget)
  assert.equal(readlinkSync(app), packageRoot)
})

test.after(() => rmSync(sandbox, { recursive: true, force: true }))
