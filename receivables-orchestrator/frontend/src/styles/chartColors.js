// Espelha as CSS custom properties de index.css — usado em atributos SVG do
// recharts, que nao resolvem var() de forma confiavel em todo navegador.
export const chartColors = {
  bg: "#0D0D12",
  surface: "#13131A",
  surface2: "#1A1A24",
  text: "#E8E8F0",
  textMuted: "rgba(232, 232, 240, 0.55)",
  border: "rgba(255, 255, 255, 0.08)",
  accent: "#6C63FF",
  accent2: "#00D4AA",
  danger: "#FF4D6D",
  warning: "#FFB020",
  success: "#00C896",
};

export const seriesPalette = [chartColors.accent, chartColors.accent2, chartColors.warning, chartColors.danger];
