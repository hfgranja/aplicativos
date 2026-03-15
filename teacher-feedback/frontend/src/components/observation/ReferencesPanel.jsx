import { C } from '../../colors'
import { Input, Textarea, Button } from '../shared'

const RESPONSIBLE_OPTIONS = ['professor', 'pec', 'ambos']

export function ReferencesPanel({ state, set, addBnccSkill, removeBnccSkill, addAction, setAction, removeAction }) {
  return (
    <div>
      <h2 style={{ color: C.accent2, fontSize: 16, marginBottom: 8, fontWeight: 700 }}>
        Referências e Próximos Passos
      </h2>

      {/* BNCC Skills */}
      <div style={{ marginBottom: 24 }}>
        <p style={{ color: C.textMuted, fontSize: 12, marginBottom: 10 }}>
          Habilidades BNCC trabalhadas na aula (adicione os códigos):
        </p>
        <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
          <input
            value={state.bncc_input}
            onChange={e => set('bncc_input', e.target.value)}
            onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addBnccSkill())}
            placeholder="Ex: EF06MA01"
            style={{
              flex: 1, background: C.surface2, border: `1px solid ${C.border}`,
              borderRadius: 8, padding: '9px 14px', color: C.text,
              fontFamily: 'JetBrains Mono', fontSize: 13,
            }}
          />
          <Button onClick={addBnccSkill} variant="secondary">Adicionar</Button>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {state.bncc_skills.map(s => (
            <span
              key={s}
              style={{
                background: C.accent + '22', color: C.accent, borderRadius: 6,
                padding: '4px 10px', fontSize: 12, fontWeight: 600, cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 6,
              }}
            >
              {s}
              <span onClick={() => removeBnccSkill(s)} style={{ color: C.danger, cursor: 'pointer', fontWeight: 700 }}>×</span>
            </span>
          ))}
        </div>
      </div>

      {/* SEDUC Materials */}
      <Textarea
        label="Materiais e recursos da SEDUC utilizados"
        value={state.seduc_materials}
        onChange={v => set('seduc_materials', v)}
        rows={2}
        placeholder="Cadernos do Aluno, Plataforma SP Faz Escola, sequências didáticas..."
      />

      {/* Next observation */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
        <Input
          label="Data da próxima observação"
          type="date"
          value={state.next_observation_date}
          onChange={v => set('next_observation_date', v)}
        />
        <Input
          label="Foco da próxima observação"
          value={state.next_observation_focus}
          onChange={v => set('next_observation_focus', v)}
          placeholder="Ex: Avaliação formativa"
        />
      </div>

      {/* Combined actions */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <p style={{ color: C.textMuted, fontSize: 12 }}>Combinados (ações acordadas):</p>
          <Button onClick={addAction} variant="ghost" style={{ fontSize: 12, padding: '6px 12px' }}>
            + Adicionar
          </Button>
        </div>
        {state.combined_actions.map((act, i) => (
          <div
            key={i}
            style={{
              background: C.surface2, borderRadius: 8, padding: 14, marginBottom: 10,
              border: `1px solid ${C.border}`,
            }}
          >
            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto auto', gap: 10, alignItems: 'center' }}>
              <input
                value={act.action}
                onChange={e => setAction(i, 'action', e.target.value)}
                placeholder="Descreva a ação combinada..."
                style={{
                  background: C.surface3, border: `1px solid ${C.border}`, borderRadius: 6,
                  padding: '8px 12px', color: C.text, fontFamily: 'JetBrains Mono', fontSize: 12,
                }}
              />
              <select
                value={act.responsible}
                onChange={e => setAction(i, 'responsible', e.target.value)}
                style={{
                  background: C.surface3, border: `1px solid ${C.border}`, borderRadius: 6,
                  padding: '8px 10px', color: C.text, fontFamily: 'JetBrains Mono', fontSize: 12,
                }}
              >
                <option value="professor">Professor</option>
                <option value="pec">PEC</option>
                <option value="ambos">Ambos</option>
              </select>
              <input
                type="date"
                value={act.deadline}
                onChange={e => setAction(i, 'deadline', e.target.value)}
                style={{
                  background: C.surface3, border: `1px solid ${C.border}`, borderRadius: 6,
                  padding: '8px 10px', color: C.text, fontFamily: 'JetBrains Mono', fontSize: 12,
                }}
              />
            </div>
            <button
              type="button"
              onClick={() => removeAction(i)}
              style={{ background: 'none', border: 'none', color: C.danger, cursor: 'pointer', fontSize: 11, marginTop: 6 }}
            >
              Remover
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
