import { C } from '../../colors'
import { Input, Select, Textarea, Button } from '../shared'

const RESPONSIBLE_OPTIONS = [
  { value: 'professor', label: 'Professor(a)' },
  { value: 'escola', label: 'Escola/Coordenação' },
  { value: 'familia', label: 'Família' },
  { value: 'rede', label: 'Rede de Apoio (CEFAI, etc.)' },
]

export function EF1EncaminhamentosPanel({ state, set, addEf1Encaminhamento, setEf1Encaminhamento, removeEf1Encaminhamento }) {
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
        <span style={{
          background: '#A78BFA22', color: '#A78BFA', border: '1px solid #A78BFA55',
          borderRadius: 6, padding: '3px 10px', fontSize: 11, fontWeight: 700,
        }}>
          EF I
        </span>
        <h2 style={{ color: '#A78BFA', fontSize: 16, fontWeight: 700, margin: 0 }}>
          Sugestões e Encaminhamentos
        </h2>
      </div>

      {/* Free text suggestions */}
      <Textarea
        label="Sugestões ao professor (texto livre)"
        value={state.ef1_sugestoes}
        onChange={v => set('ef1_sugestoes', v)}
        placeholder="Sugestões pedagógicas, formativas ou de apoio ao professor..."
        rows={4}
      />

      {/* Structured encaminhamentos */}
      <div style={{ marginTop: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <p style={{ color: C.textMuted, fontSize: 12, fontWeight: 700, margin: 0 }}>
            Encaminhamentos formais
          </p>
          <Button onClick={addEf1Encaminhamento} variant="secondary" style={{ fontSize: 12, padding: '6px 14px' }}>
            + Adicionar
          </Button>
        </div>

        {state.ef1_encaminhamentos.length === 0 && (
          <div style={{ textAlign: 'center', padding: '24px 0', color: C.textMuted, fontSize: 13, background: C.surface2, borderRadius: 8 }}>
            Nenhum encaminhamento adicionado.
          </div>
        )}

        {state.ef1_encaminhamentos.map((enc, i) => (
          <div key={i} style={{
            background: C.surface2, borderRadius: 10, padding: 16, marginBottom: 12,
            border: `1px solid ${C.border}`,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
              <span style={{ color: '#A78BFA', fontSize: 12, fontWeight: 700 }}>Encaminhamento #{i + 1}</span>
              <button
                type="button"
                onClick={() => removeEf1Encaminhamento(i)}
                style={{ background: 'none', border: 'none', color: C.danger, cursor: 'pointer', fontSize: 13, padding: 0 }}
              >
                ✕
              </button>
            </div>
            <Textarea
              label="Descrição do encaminhamento"
              value={enc.encaminhamento}
              onChange={v => setEf1Encaminhamento(i, 'encaminhamento', v)}
              placeholder="Ex: Encaminhar para avaliação psicopedagógica, ATPC temática, etc."
              rows={2}
            />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 4 }}>
              <Select
                label="Responsável"
                value={enc.responsible}
                onChange={v => setEf1Encaminhamento(i, 'responsible', v)}
                options={RESPONSIBLE_OPTIONS}
              />
              <Input
                label="Prazo"
                type="date"
                value={enc.deadline}
                onChange={v => setEf1Encaminhamento(i, 'deadline', v)}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
