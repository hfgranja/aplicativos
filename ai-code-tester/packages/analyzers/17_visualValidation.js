export default function visualValidationAnalysis(code) {
  const issues = []
  const suggestions = []
  let deductions = 0

  try {
    // Only fully applicable to JSX/HTML code
    const isJSX = /<[A-Z][a-zA-Z]*|<[a-z]+(>|\s)/.test(code)
    const hasReact = /import React|from ['"]react['"]|useState|useEffect|\.jsx|\.tsx/.test(code)
    const isHTML = /<html|<body|<div|<button|<input/.test(code)

    if (!isJSX && !isHTML) {
      return {
        id: 17,
        name: 'Validação Visual Automatizada',
        icon: '👁️',
        color: '#00B894',
        score: 85,
        issues: [],
        suggestions: ['Técnica aplicável a código React/JSX ou HTML com elementos visuais interativos'],
        detail: 'Sem componentes visuais detectados',
      }
    }

    // 1. <button> without aria-label or meaningful text
    const buttonMatches = code.match(/<button[^>]*>/g) || []
    const buttonsWithoutA11y = buttonMatches.filter(btn =>
      !btn.includes('aria-label') && !btn.includes('aria-labelledby')
    )
    if (buttonsWithoutA11y.length > 0) {
      deductions += buttonsWithoutA11y.length * 8
      issues.push(`${buttonsWithoutA11y.length} <button> sem aria-label — inacessível a leitores de tela`)
      suggestions.push('Adicione aria-label em botões sem texto visível: <button aria-label="Fechar">')
    }

    // 2. <img> without alt attribute
    const imgMatches = code.match(/<img[^>]*>/g) || []
    const imgsWithoutAlt = imgMatches.filter(img => !img.includes(' alt=') && !img.includes(' alt ='))
    if (imgsWithoutAlt.length > 0) {
      deductions += imgsWithoutAlt.length * 10
      issues.push(`${imgsWithoutAlt.length} <img> sem atributo alt — viola WCAG 2.1 Nível A`)
      suggestions.push('Adicione alt descritivo: <img alt="Descrição da imagem" /> ou alt="" para imagens decorativas')
    }

    // 3. <input> without label
    const inputMatches = code.match(/<input[^>]*>/g) || []
    const inputsWithoutLabel = inputMatches.filter(inp =>
      inp.includes('type="text"') || inp.includes('type="email"') || inp.includes("type='text'") ||
      inp.includes('type="password"') || !inp.includes('type=')
    ).filter(inp =>
      !inp.includes('aria-label') && !inp.includes('htmlFor') && !inp.includes('id=')
    )
    if (inputsWithoutLabel.length > 0) {
      deductions += inputsWithoutLabel.length * 8
      issues.push(`${inputsWithoutLabel.length} <input> sem label/aria-label associado`)
      suggestions.push('Use <label htmlFor="id"> + <input id="id"> ou <input aria-label="Campo">')
    }

    // 4. onClick on div without role (keyboard inaccessible)
    const divOnClick = (code.match(/<div[^>]*onClick[^>]*>/g) || [])
      .filter(d => !d.includes('role='))
    if (divOnClick.length > 0) {
      deductions += divOnClick.length * 6
      issues.push(`${divOnClick.length} <div onClick> sem role — não operável por teclado`)
      suggestions.push('Use <button> ao invés de <div onClick> ou adicione role="button" + onKeyPress')
    }

    // 5. Missing data-testid for interactive elements
    const interactiveElements = (code.match(/<(button|input|select|textarea|a\s)[^>]*>/g) || []).length
    const testIds = (code.match(/data-testid=/g) || []).length
    if (interactiveElements > 3 && testIds === 0) {
      deductions += 12
      issues.push(`${interactiveElements} elemento(s) interativo(s) sem data-testid — dificulta testes automatizados`)
      suggestions.push('Adicione data-testid aos elementos principais para facilitar testes: data-testid="btn-submit"')
    }

    // 6. Missing visual testing library imports
    const hasTestingLib = /@testing-library|jest-dom|cypress|playwright|storybook|chromatic|percy|vitest/.test(code)
    if (!hasTestingLib && (hasReact || isJSX)) {
      deductions += 15
      issues.push('Nenhuma biblioteca de testes visuais detectada (@testing-library, Cypress, Playwright, Storybook)')
      suggestions.push('Adicione @testing-library/react para testes de componentes, ou Storybook para visual review')
    }

    // 7. hardcoded colors without CSS variables (maintainability/theme issue)
    const hardcodedColors = (code.match(/#[0-9A-Fa-f]{3,6}\b|rgb\(|rgba\(/g) || []).length
    if (hardcodedColors > 5) {
      deductions += Math.min(hardcodedColors * 2, 10)
      issues.push(`${hardcodedColors} cor(es) hardcoded detectada(s) — dificulta theming e dark mode`)
      suggestions.push('Use variáveis CSS (--color-primary) ou tokens de design ao invés de cores hardcoded')
    }

    // 8. Missing responsive meta or media queries
    const hasMediaQuery = /@media|clamp\(|min\(|max\(|vw|vh|vmin|vmax/.test(code)
    const hasResponsivePatterns = /flexWrap|gridTemplateColumns|minWidth|maxWidth/.test(code)
    if (!hasMediaQuery && !hasResponsivePatterns && isJSX) {
      deductions += 8
      issues.push('Sem media queries ou padrões responsivos detectados — layout pode quebrar em mobile')
      suggestions.push('Adicione @media queries ou use flexbox/grid com minWidth/maxWidth para responsividade')
    }

    const finalScore = Math.max(0, 100 - deductions)
    const a11yIssues = buttonsWithoutA11y.length + imgsWithoutAlt.length + inputsWithoutLabel.length
    return {
      id: 17,
      name: 'Validação Visual Automatizada',
      icon: '👁️',
      color: '#00B894',
      score: finalScore,
      issues: issues.slice(0, 8),
      suggestions: suggestions.slice(0, 4),
      detail: `${a11yIssues} problema(s) de acessibilidade · ${testIds} test IDs`,
    }
  } catch {
    return {
      id: 17,
      name: 'Validação Visual Automatizada',
      icon: '👁️',
      color: '#00B894',
      score: 50,
      issues: ['Não foi possível analisar o código'],
      suggestions: [],
      detail: '—',
    }
  }
}
