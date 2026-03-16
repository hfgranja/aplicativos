export const COLORS = {
  bg: '#0D0D12',
  surface: '#13131A',
  surface2: '#1A1A24',
  surface3: '#22223A',
  border: 'rgba(255,255,255,0.08)',
  text: '#E8E8F0',
  textMuted: 'rgba(232,232,240,0.5)',
  accent: '#6C63FF',
  accent2: '#00D4AA',
  danger: '#FF4D6D',
  warning: '#FFB020',
  success: '#00C896',
}

export const TECHNIQUE_COLORS = [
  '#6C63FF', // 1 Static Analysis
  '#00D4AA', // 2 Complexity
  '#FF6B6B', // 3 Duplication
  '#FF4D6D', // 4 Security
  '#FFB020', // 5 Type Safety
  '#4ECDC4', // 6 Dependencies
  '#45B7D1', // 7 Coverage
  '#96CEB4', // 8 Documentation
  '#FFEAA7', // 9 Best Practices
  '#DDA0DD', // 10 Performance
  '#98D8C8', // 11 Error Handling
  '#F0A500', // 12 API Contracts
]

export function scoreColor(score) {
  if (score >= 80) return COLORS.success
  if (score >= 60) return COLORS.warning
  return COLORS.danger
}
