import { useAnalysis } from '../hooks/useAnalysis.js'
import StepNav from './StepNav.jsx'
import CodeInput from './CodeInput.jsx'
import AnalysisProgress from './AnalysisProgress.jsx'
import ResultsDashboard from './ResultsDashboard.jsx'
import TestGenerator from './TestGenerator.jsx'

export default function AiCodeTester() {
  const {
    step, code, packageJson, progress, currentTechnique,
    results, overallScore, generatedTests, error,
    setCode, setPkg, startAnalysis, generateTestSuite, reset,
    git, connectGit, disconnectGit, setSelectedFiles, loadAndAnalyze,
    advisor, updateAdvisorConfig,
  } = useAnalysis()

  return (
    <div style={{ minHeight: '100vh', background: '#0D0D12', color: '#E8E8F0' }}>
      {/* Header */}
      <header style={{
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        padding: '20px 40px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        position: 'sticky', top: 0, zIndex: 100,
        background: 'rgba(13,13,18,0.9)',
        backdropFilter: 'blur(12px)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{
            width: 38, height: 38, borderRadius: 10,
            background: 'linear-gradient(135deg, #6C63FF, #00D4AA)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 18,
          }}>
            🤖
          </div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, letterSpacing: 0.5 }}>
              AI Code Tester
            </div>
            <div style={{ fontSize: 11, color: 'rgba(232,232,240,0.4)', letterSpacing: 0.5 }}>
              Validação com 13 Técnicas Globais
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          {[
            { label: 'Análise Estática', color: '#6C63FF' },
            { label: 'Segurança', color: '#FF4D6D' },
            { label: 'Performance', color: '#DDA0DD' },
            { label: 'Testes Auto', color: '#00D4AA' },
          ].map(tag => (
            <span key={tag.label} style={{
              fontSize: 10, padding: '3px 10px', borderRadius: 20,
              background: `${tag.color}15`, border: `1px solid ${tag.color}30`,
              color: tag.color, fontWeight: 600, letterSpacing: 0.5,
              display: 'none',
            }}>
              {tag.label}
            </span>
          ))}

          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            style={{
              fontSize: 11, padding: '5px 12px', borderRadius: 6,
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
              color: 'rgba(232,232,240,0.5)',
              textDecoration: 'none', fontWeight: 500,
            }}
          >
            13 Técnicas
          </a>
        </div>
      </header>

      {/* Hero section — only on input step */}
      {step === 'input' && (
        <div style={{
          textAlign: 'center', padding: '52px 40px 48px',
          background: 'radial-gradient(ellipse 60% 40% at 50% 0%, rgba(108,99,255,0.12) 0%, transparent 70%)',
        }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            background: 'rgba(108,99,255,0.1)', border: '1px solid rgba(108,99,255,0.25)',
            borderRadius: 20, padding: '5px 16px', marginBottom: 24,
            fontSize: 11, color: '#6C63FF', fontWeight: 600, letterSpacing: 1,
          }}>
            ✨ POWERED BY AST ANALYSIS
          </div>
          <h1 style={{
            fontSize: 'clamp(28px, 5vw, 48px)', fontWeight: 800,
            lineHeight: 1.15, marginBottom: 16, letterSpacing: -0.5,
          }}>
            Valide seu código gerado por IA
            <br />
            <span style={{ background: 'linear-gradient(90deg, #6C63FF, #00D4AA)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              com 13 técnicas profissionais
            </span>
          </h1>
          <p style={{ fontSize: 16, color: 'rgba(232,232,240,0.5)', maxWidth: 560, margin: '0 auto 16px', lineHeight: 1.7 }}>
            Análise completa: segurança, complexidade, cobertura, boas práticas e mais.
            Conecte repositórios Git ou cole o código diretamente.
          </p>

          {/* Technique pills */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center', maxWidth: 720, margin: '0 auto 0' }}>
            {TECHNIQUES_LIST.map((t, i) => (
              <span key={i} style={{
                fontSize: 11, padding: '4px 12px', borderRadius: 20,
                background: `${t.color}12`, border: `1px solid ${t.color}25`,
                color: t.color, fontWeight: 500,
              }}>
                {t.icon} {t.name}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Main content */}
      <main style={{
        maxWidth: 1080, margin: '0 auto',
        padding: step === 'input' ? '0 40px 60px' : '40px 40px 60px',
      }}>
        <StepNav currentStep={step} />

        {step === 'input' && (
          <CodeInput
            code={code}
            packageJson={packageJson}
            onCodeChange={setCode}
            onPkgChange={setPkg}
            onAnalyze={startAnalysis}
            error={error}
            git={git}
            onConnectGit={connectGit}
            onDisconnectGit={disconnectGit}
            onSelectFiles={setSelectedFiles}
            onLoadAndAnalyze={loadAndAnalyze}
            connectingGit={git.connecting}
            connectionError={git.connectionError}
          />
        )}

        {step === 'analyzing' && (
          <AnalysisProgress progress={progress} currentTechnique={currentTechnique} />
        )}

        {step === 'results' && (
          <ResultsDashboard
            results={results}
            overallScore={overallScore}
            onGenerateTests={generateTestSuite}
            onReset={reset}
            advisor={advisor}
            onAdvisorConfigUpdate={updateAdvisorConfig}
          />
        )}

        {step === 'tests' && (
          <TestGenerator
            generatedTests={generatedTests}
            overallScore={overallScore}
            onReset={reset}
          />
        )}
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid rgba(255,255,255,0.05)',
        padding: '16px 40px',
        textAlign: 'center',
        fontSize: 11, color: 'rgba(232,232,240,0.25)',
        display: 'flex', justifyContent: 'center', gap: 24, flexWrap: 'wrap',
      }}>
        <span>AI Code Tester v1.0</span>
        <span>13 Técnicas de Validação</span>
        <span>GitHub · GitLab · Bitbucket · Azure DevOps</span>
        <span>Análise 100% no browser · sem envio de dados</span>
      </footer>
    </div>
  )
}

const TECHNIQUES_LIST = [
  { name: 'Análise Estática', icon: '🔍', color: '#6C63FF' },
  { name: 'Complexidade', icon: '🔄', color: '#00D4AA' },
  { name: 'Duplicação', icon: '📋', color: '#FF6B6B' },
  { name: 'Segurança', icon: '🛡️', color: '#FF4D6D' },
  { name: 'Tipos', icon: '📐', color: '#FFB020' },
  { name: 'Dependências', icon: '📦', color: '#4ECDC4' },
  { name: 'Cobertura', icon: '📊', color: '#45B7D1' },
  { name: 'Documentação', icon: '📝', color: '#96CEB4' },
  { name: 'Boas Práticas', icon: '⚡', color: '#FFEAA7' },
  { name: 'Performance', icon: '🚀', color: '#DDA0DD' },
  { name: 'Erros', icon: '🔧', color: '#98D8C8' },
  { name: 'API Contracts', icon: '🔌', color: '#F0A500' },
  { name: 'Mutação', icon: '🧬', color: '#E040FB' },
]
