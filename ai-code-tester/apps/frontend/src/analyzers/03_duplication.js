/**
 * Técnica 3: Detecção de Duplicação de Código (DRY)
 * Usa fingerprinting de tokens para detectar blocos similares
 */

function tokenize(line) {
  return line.trim()
    .replace(/['"`][^'"]*['"`]/g, 'STR')
    .replace(/\b\d+\b/g, 'NUM')
    .replace(/\b(const|let|var)\b/g, 'DECL')
}

function makeChunks(lines, size = 6) {
  const chunks = []
  for (let i = 0; i <= lines.length - size; i++) {
    const chunk = lines.slice(i, i + size).map(tokenize).join('\n')
    chunks.push({ chunk, start: i + 1, end: i + size })
  }
  return chunks
}

export default function duplicationAnalysis(code) {
  const issues = []
  const suggestions = []

  const lines = code.split('\n').filter(l => l.trim().length > 2)
  if (lines.length < 12) {
    return {
      id: 3, name: 'Duplicação de Código', icon: '📋', color: '#FF6B6B',
      score: 100, issues: ['Código muito curto para análise de duplicação'],
      suggestions: ['Adicione mais código para uma análise completa'], detail: 'N/A',
    }
  }

  const chunks = makeChunks(lines, 5)
  const seen = new Map()
  const duplicates = []

  chunks.forEach(({ chunk, start, end }) => {
    if (seen.has(chunk)) {
      duplicates.push({ original: seen.get(chunk), dupe: { start, end } })
    } else {
      seen.set(chunk, { start, end })
    }
  })

  const uniqueDupes = duplicates.slice(0, 5)
  uniqueDupes.forEach(({ original, dupe }) => {
    issues.push(`Bloco duplicado: linhas ${original.start}-${original.end} ≈ linhas ${dupe.start}-${dupe.end}`)
  })

  const dupeRatio = duplicates.length / Math.max(1, chunks.length)
  const score = Math.round(Math.max(0, 100 - dupeRatio * 200))

  if (duplicates.length === 0) {
    suggestions.push('Sem duplicação significativa detectada — bom princípio DRY')
  } else {
    suggestions.push('Extraia blocos repetidos para funções utilitárias reutilizáveis')
    suggestions.push('Considere usar HOF (Higher-Order Functions) para padrões repetidos')
    suggestions.push('Use hooks customizados para lógica React duplicada')
  }

  return {
    id: 3,
    name: 'Duplicação de Código',
    icon: '📋',
    color: '#FF6B6B',
    score,
    issues: issues.slice(0, 8),
    suggestions,
    detail: `${duplicates.length} bloco(s) duplicado(s) de ${chunks.length} verificados`,
  }
}
