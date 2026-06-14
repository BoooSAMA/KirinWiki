import { COLOR_PALETTE, hexBrightness } from './colorPalette'

let rafId = null
let lastTimeCheck = 0
let currentColor = null

function getSingaporeTime() {
  try {
    const parts = new Intl.DateTimeFormat('en-SG', {
      timeZone: 'Asia/Singapore',
      hour: 'numeric',
      minute: 'numeric',
      hourCycle: 'h23',
    }).format(new Date())

    const match = parts.match(/(\d{1,2}):(\d{2})/)
    if (!match) throw new Error('Unexpected time format')

    return { hour: parseInt(match[1], 10) % 24, minute: parseInt(match[2], 10) }
  } catch {
    // Fallback: manual UTC+8 offset
    const now = new Date()
    const hour = (now.getUTCHours() + 8) % 24
    const minute = now.getUTCMinutes()
    return { hour, minute }
  }
}

function lerpChannel(c1, c2, t) {
  return Math.round(c1 + (c2 - c1) * t)
}

function hexToRgb(hex) {
  return {
    r: parseInt(hex.slice(1, 3), 16),
    g: parseInt(hex.slice(3, 5), 16),
    b: parseInt(hex.slice(5, 7), 16),
  }
}

function interpolateColor(hour, minute) {
  const current = hexToRgb(COLOR_PALETTE[hour])
  const next = hexToRgb(COLOR_PALETTE[(hour + 1) % 24])
  const fraction = minute / 60

  const r = lerpChannel(current.r, next.r, fraction)
  const g = lerpChannel(current.g, next.g, fraction)
  const b = lerpChannel(current.b, next.b, fraction)

  return '#' + [r, g, b].map(c => c.toString(16).padStart(2, '0')).join('')
}

function applyColor(hex) {
  // 1. Update 3D scene background
  if (window.__setSceneBackground) {
    window.__setSceneBackground(hex)
  }

  // 2. Update CSS body background and custom property
  document.body.style.backgroundColor = hex
  document.documentElement.style.setProperty('--time-bg-color', hex)

  // 3. Set data-theme attribute for dark mode toggling
  const brightness = hexBrightness(hex)
  if (brightness < 0.5) {
    document.documentElement.dataset.theme = 'night'
  } else {
    delete document.documentElement.dataset.theme
  }

  currentColor = hex
}

function loop(timestamp) {
  // Check time every 60 seconds
  if (!lastTimeCheck || timestamp - lastTimeCheck > 60000) {
    lastTimeCheck = timestamp
    const { hour, minute } = getSingaporeTime()
    currentColor = interpolateColor(hour, minute)
  }

  // Apply the current interpolated color every frame
  if (currentColor) {
    applyColor(currentColor)
  }

  rafId = requestAnimationFrame(loop)
}

export function init() {
  // Immediate initial apply (don't wait for first RAF)
  const { hour, minute } = getSingaporeTime()
  currentColor = interpolateColor(hour, minute)
  applyColor(currentColor)

  // Start the RAF loop
  rafId = requestAnimationFrame(loop)

  // Handle visibility change: re-sync time when page becomes visible
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      const { hour, minute } = getSingaporeTime()
      currentColor = interpolateColor(hour, minute)
      lastTimeCheck = 0 // force time re-check in next loop tick
    }
  })
}
