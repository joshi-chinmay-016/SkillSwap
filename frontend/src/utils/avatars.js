// A curated collection of avatar options for new users.
// Uses inline SVG data URIs so they work offline without external APIs.

const AVATAR_COLORS = [
  ["#6366f1", "#818cf8"], // indigo
  ["#ec4899", "#f472b6"], // pink
  ["#f97316", "#fb923c"], // orange
  ["#10b981", "#34d399"], // emerald
  ["#8b5cf6", "#a78bfa"], // violet
  ["#ef4444", "#f87171"], // red
  ["#06b6d4", "#22d3ee"], // cyan
  ["#f59e0b", "#fbbf24"], // amber
  ["#14b8a6", "#2dd4bf"], // teal
  ["#e11d48", "#fb7185"], // rose
  ["#3b82f6", "#60a5fa"], // blue
  ["#84cc16", "#a3e635"], // lime
];

const AVATAR_EMOJIS = [
  "🦊", "🐱", "🐶", "🦁", "🐼", "🐨",
  "🦄", "🐸", "🦉", "🐯", "🐧", "🐙",
];

function createAvatarSvg(emoji, bgColor1, bgColor2) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <defs>
      <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:${bgColor1}"/>
        <stop offset="100%" style="stop-color:${bgColor2}"/>
      </linearGradient>
    </defs>
    <rect width="100" height="100" rx="50" fill="url(#bg)"/>
    <text x="50" y="58" text-anchor="middle" dominant-baseline="middle" font-size="48">${emoji}</text>
  </svg>`;
  return `data:image/svg+xml,${encodeURIComponent(svg)}`;
}

export const AVATAR_OPTIONS = AVATAR_EMOJIS.map((emoji, i) => ({
  id: `avatar-${i}`,
  emoji,
  url: createAvatarSvg(emoji, AVATAR_COLORS[i][0], AVATAR_COLORS[i][1]),
  colors: AVATAR_COLORS[i],
}));

export default AVATAR_OPTIONS;
