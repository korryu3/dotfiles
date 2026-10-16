import { atom, read, update } from 'claude-code'
import type { Register, SessionContextUsage, SessionRateLimit } from 'claude-code'

import type { UsageSnapshot } from '../types'

const snapshot = atom({ plugin: 'usage-band', key: 'snapshot' } as const, null)

const BRAILLE = '⠀⣀⣄⣤⣦⣶⣷⣿'
const BAR_WIDTH = 8

const toSnapshot = (
  context: SessionContextUsage,
  rateLimits: SessionRateLimit[],
): UsageSnapshot => {
  const five = rateLimits.find(limit => limit.kind === 'five_hour')

  return {
    ctxPercent: context.percent,
    fiveHour: five && { percentUsed: five.percentUsed, resetsAt: five.resetsAt },
  }
}

const brailleBar = (pct: number): string => {
  const level = Math.min(Math.max(pct, 0), 100) / 100
  let bar = ''
  for (let i = 0; i < BAR_WIDTH; i++) {
    const start = i / BAR_WIDTH
    const end = (i + 1) / BAR_WIDTH
    if (level >= end) {
      bar += BRAILLE[7]
    } else if (level <= start) {
      bar += BRAILLE[0]
    } else {
      bar += BRAILLE[Math.min(Math.floor(((level - start) / (end - start)) * 7), 7)]
    }
  }

  return bar
}

const levelColor = (pct: number) =>
  pct <= 30 ? 'success' : pct <= 60 ? 'warning' : 'error'

const formatHHMM = (iso: string): string | undefined => {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return undefined
  }
  const pad = (n: number) => String(n).padStart(2, '0')

  return `${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const { context, rateLimits } = await $.session.usage()
    await update($, snapshot, () => toSnapshot(context, rateLimits))

    return next(e)
  })

  on('session.measure', async ($, e, next) => {
    await update($, snapshot, () => toSnapshot(e.context, e.rateLimits))

    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const snap = await read($, snapshot)
    const ctx = snap?.ctxPercent
    const five = snap?.fiveHour
    if (e.props.hasSurvey || (ctx === undefined && five === undefined)) {
      return next(e)
    }

    const { Box, Text } = $.ui.resolve(e)
    const meter = (label: string, pct: number) => (
      <Text>
        <Text dimColor>{label} </Text>
        <Text color={levelColor(pct)}>
          {brailleBar(pct)} {Math.round(pct)}%
        </Text>
      </Text>
    )
    const reset = five?.resetsAt && formatHHMM(five.resetsAt)

    return (
      <Box>
        {ctx !== undefined && meter('ctx', ctx)}
        {ctx !== undefined && five !== undefined && <Text>{'   '}</Text>}
        {five !== undefined && meter('5h', five.percentUsed)}
        {reset && <Text dimColor> @{reset}</Text>}
      </Box>
    )
  })
}
