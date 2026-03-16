/**
 * Técnica 4: Varredura de Vulnerabilidades de Segurança
 * Detecta: eval, innerHTML, dangerouslySetInnerHTML, secrets hardcoded,
 * SQL injection patterns, prototype pollution, open redirect
 */

const SECURITY_PATTERNS = [
  {
    pattern: /\beval\s*\(/g,
    severity: 'CRÍTICO',
    msg: 'eval() detectado — execução de código arbitrário (RCE)',
    score: -20,
  },
  {
    pattern: /\.innerHTML\s*=/g,
    severity: 'ALTO',
    msg: 'innerHTML= — risco de XSS (use textContent ou sanitização)',
    score: -15,
  },
  {
    pattern: /dangerouslySetInnerHTML/g,
    severity: 'ALTO',
    msg: 'dangerouslySetInnerHTML — risco XSS se não sanitizado',
    score: -10,
  },
  {
    pattern: /document\.write\s*\(/g,
    severity: 'ALTO',
    msg: 'document.write() — obsoleto e perigoso para XSS',
    score: -10,
  },
  {
    pattern: /(password|passwd|secret|api_key|apikey|token|auth)\s*[:=]\s*['"][^'"]{4,}/gi,
    severity: 'CRÍTICO',
    msg: 'Credencial hardcoded detectada — use variáveis de ambiente',
    score: -25,
  },
  {
    pattern: /SELECT\s+\*?\s+FROM.*\+|INSERT\s+INTO.*\+|DELETE\s+FROM.*\+/gi,
    severity: 'CRÍTICO',
    msg: 'Possível SQL Injection — use prepared statements / ORM',
    score: -20,
  },
  {
    pattern: /require\s*\(\s*[^'"]/g,
    severity: 'MÉDIO',
    msg: 'require() dinâmico — pode carregar módulos arbitrários',
    score: -8,
  },
  {
    pattern: /\.__proto__\s*=/g,
    severity: 'CRÍTICO',
    msg: 'Prototype pollution detectada — risco de modificar Object.prototype',
    score: -20,
  },
  {
    pattern: /window\.location\s*=\s*(?!['"]\/)/g,
    severity: 'MÉDIO',
    msg: 'Possível open redirect — valide destino antes de redirecionar',
    score: -8,
  },
  {
    pattern: /setTimeout\s*\(\s*['"`][^'"]+['"`]/g,
    severity: 'ALTO',
    msg: 'setTimeout com string — equivalente a eval()',
    score: -12,
  },
  {
    pattern: /new\s+Function\s*\(/g,
    severity: 'ALTO',
    msg: 'new Function() — execução dinâmica de código',
    score: -15,
  },
  {
    pattern: /localStorage\.setItem.*password|sessionStorage.*password/gi,
    severity: 'ALTO',
    msg: 'Senha armazenada em localStorage/sessionStorage — inseguro',
    score: -15,
  },
]

export default function securityScan(code) {
  const issues = []
  const suggestions = []
  let deductions = 0
  const lines = code.split('\n')

  SECURITY_PATTERNS.forEach(({ pattern, severity, msg, score }) => {
    lines.forEach((line, i) => {
      if (pattern.test(line)) {
        issues.push(`[${severity}] Linha ${i + 1}: ${msg}`)
        deductions += Math.abs(score)
      }
      pattern.lastIndex = 0 // reset regex state
    })
  })

  const finalScore = Math.max(0, 100 - deductions)

  if (issues.length === 0) {
    suggestions.push('Nenhuma vulnerabilidade crítica detectada')
    suggestions.push('Execute SAST completo (Snyk, SonarQube) para análise aprofundada')
  } else {
    suggestions.push('Sanitize todas as entradas de usuário antes de exibir no DOM')
    suggestions.push('Use Content Security Policy (CSP) no servidor')
    suggestions.push('Nunca armazene credenciais no código — use .env e secrets manager')
    suggestions.push('Execute npm audit para verificar dependências vulneráveis')
  }

  return {
    id: 4,
    name: 'Varredura de Segurança',
    icon: '🛡️',
    color: '#FF4D6D',
    score: finalScore,
    issues: issues.slice(0, 10),
    suggestions,
    detail: `${issues.length} vulnerabilidade(s) encontrada(s)`,
  }
}
