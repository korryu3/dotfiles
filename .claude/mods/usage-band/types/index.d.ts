export type UsageSnapshot = {
  ctxPercent?: number
  fiveHour?: { percentUsed: number; resetsAt?: string }
}

declare module 'claude-code' {
  interface PluginState {
    'usage-band': { snapshot: UsageSnapshot | null }
  }
}
