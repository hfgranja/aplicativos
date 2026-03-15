import { C } from '../../colors'
import { Textarea, Input } from '../shared'

export function NarrativePanel({ state, set, setArrayItem }) {
  return (
    <div>
      <h2 style={{ color: C.accent2, fontSize: 16, marginBottom: 24, fontWeight: 700 }}>
        Narrativa do PEC
      </h2>

      <div style={{ marginBottom: 24 }}>
        <p style={{ color: C.textMuted, fontSize: 12, marginBottom: 12 }}>
          Principais pontos fortes identificados (máx. 3):
        </p>
        {state.pontos_fortes.map((pf, i) => (
          <Input
            key={i}
            placeholder={`Ponto forte ${i + 1}`}
            value={pf}
            onChange={v => setArrayItem('pontos_fortes', i, v)}
          />
        ))}
      </div>

      <div style={{ marginBottom: 24 }}>
        <p style={{ color: C.textMuted, fontSize: 12, marginBottom: 12 }}>
          Aspectos que podem ser aprimorados (máx. 3):
        </p>
        {state.focos_desenvolvimento.map((fd, i) => (
          <Input
            key={i}
            placeholder={`Foco de desenvolvimento ${i + 1}`}
            value={fd}
            onChange={v => setArrayItem('focos_desenvolvimento', i, v)}
          />
        ))}
      </div>

      <Textarea
        label="Sugestões preliminares"
        value={state.sugestoes}
        onChange={v => set('sugestoes', v)}
        rows={4}
        placeholder="Sugestões gerais para o professor..."
      />

      <Textarea
        label="Habilidades do Currículo Paulista trabalhadas na aula"
        value={state.habilidades_curriculo}
        onChange={v => set('habilidades_curriculo', v)}
        rows={2}
        placeholder="Ex: EF06MA01, EF06LP02..."
      />
    </div>
  )
}
