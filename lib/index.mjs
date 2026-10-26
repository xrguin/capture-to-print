/**
 * capture-to-print — DSH host half.
 *
 * The skill and the CAD runner are plain files; this plugin only makes them
 * discoverable:
 *   1. links `skills/capture-to-print` into `$DSH_HOME/skills` so the catalog
 *      finds it, and
 *   2. links the package root to `$CAPTURE_TO_PRINT_HOME/app` so
 *      `scripts/bootstrap.sh` has a stable path after a pnpm install.
 *
 * It never installs OpenSCAD or Python packages and never runs CAD on its own.
 * dispose removes a link only when it still points at this package.
 */
import { existsSync, lstatSync, mkdirSync, readlinkSync, rmSync, symlinkSync } from 'node:fs'
import { homedir } from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export const name = 'capture-to-print'

const packageRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const bundledSkill = path.join(packageRoot, 'skills', 'capture-to-print')

function dshHome() {
  return process.env.DSH_HOME || path.join(homedir(), '.dsh')
}

function captureHome() {
  return process.env.CAPTURE_TO_PRINT_HOME || path.join(homedir(), '.local', 'share', 'capture-to-print')
}

function pointsTo(dest, target) {
  try {
    if (!lstatSync(dest).isSymbolicLink()) return false
    return path.resolve(path.dirname(dest), readlinkSync(dest)) === path.resolve(target)
  } catch {
    return false
  }
}

/** Link only into a free name, or refresh a link that is already ours. */
function ensureLink(target, dest) {
  mkdirSync(path.dirname(dest), { recursive: true })
  if (pointsTo(dest, target)) return 'unchanged'
  if (existsSync(dest)) return 'skipped'
  try {
    lstatSync(dest)
    return 'skipped'
  } catch {
    // free name; fall through
  }
  symlinkSync(target, dest, 'dir')
  return 'linked'
}

function removeOwnLink(target, dest) {
  if (!pointsTo(dest, target)) return false
  rmSync(dest)
  return true
}

export function apply(ctx, config) {
  const options = config ?? {}
  const skillsRoot = options.skillsRoot
    ? path.resolve(String(options.skillsRoot))
    : path.join(dshHome(), 'skills')
  const appLink = options.appLink
    ? path.resolve(String(options.appLink))
    : path.join(captureHome(), 'app')

  const skillDest = path.join(skillsRoot, 'capture-to-print')
  const results = []

  if (!existsSync(path.join(bundledSkill, 'SKILL.md'))) {
    results.push(`missing bundled skill at ${bundledSkill}`)
  } else {
    results.push(`skill ${ensureLink(bundledSkill, skillDest)}: ${skillDest}`)
  }
  results.push(`app ${ensureLink(packageRoot, appLink)}: ${appLink}`)

  const log = typeof ctx?.logger?.info === 'function' ? ctx.logger.info.bind(ctx.logger) : console.log
  log(`[capture-to-print] ${results.join(' | ')}`)

  if (typeof ctx?.on === 'function') {
    ctx.on('dispose', () => {
      removeOwnLink(bundledSkill, skillDest)
      removeOwnLink(packageRoot, appLink)
    })
  }
}
