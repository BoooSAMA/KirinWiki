// 24-hour palette keyframes, index = hour (0-23)
// Based on Singapore natural light cycle (near equator, sunrise ~06:00, sunset ~19:00)
export const COLOR_PALETTE = [
  '#0a0a1a', // 00:00 深夜墨蓝
  '#0d0d20', // 01:00
  '#0f0f25', // 02:00
  '#12122a', // 03:00
  '#1a1a3e', // 04:00 黎明前
  '#2a1a3e', // 05:00 紫粉晨曦
  '#6a3050', // 06:00 日出紫
  '#d4a060', // 07:00 晨光暖金
  '#e8d8b0', // 08:00 清晨暖白
  '#f0e8d0', // 09:00
  '#f8f4e8', // 10:00
  '#ffffff', // 11:00 正午纯白
  '#ffffff', // 12:00
  '#faf8f0', // 13:00
  '#f0ece0', // 14:00
  '#e8dcc8', // 15:00
  '#d4c098', // 16:00 午后暖黄
  '#c89060', // 17:00 黄昏暖橙
  '#b06040', // 18:00 日落橙红
  '#6a3050', // 19:00 暮色紫
  '#1a1a3e', // 20:00 入夜深蓝
  '#0d0d2b', // 21:00
  '#0a0a1a', // 22:00
  '#0a0a1a', // 23:00
]

/** Calculate brightness 0-1 from a hex color string */
export function hexBrightness(hex) {
  const r = parseInt(hex.slice(1, 3), 16) / 255
  const g = parseInt(hex.slice(3, 5), 16) / 255
  const b = parseInt(hex.slice(5, 7), 16) / 255
  return 0.299 * r + 0.587 * g + 0.114 * b
}
