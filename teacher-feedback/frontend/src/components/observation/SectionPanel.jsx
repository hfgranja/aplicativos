import { C } from '../../colors'
import { CriteriaRow } from './RatingButton'
import { Textarea } from '../shared'

const METHODOLOGIES = [
  'Aula expositiva dialogada',
  'Trabalho em grupo/duplas',
  'Resolução de exercícios',
  'Uso de recursos visuais/tecnológicos',
  'Atividades práticas/experimentais',
  'Leitura e interpretação de textos',
  'Projetos/sequências didáticas',
]

const SECTION_META = {
  s1: {
    title: '1. Planejamento e Alinhamento Curricular',
    criteria: [
      ['s1_c1', 'Plano de aula alinhado ao Currículo Paulista e materiais oficiais da SEDUC'],
      ['s1_c2', 'Objetivos de aprendizagem explícitos e claros para os alunos'],
      ['s1_c3', 'Habilidades da BNCC/Currículo Paulista adequadas ao ano/série'],
      ['s1_c4', 'Atividades coerentes com os objetivos da aula'],
    ],
  },
  s2: {
    title: '2. Condução Didática da Aula',
    criteria: [
      ['s2_c1', 'Aula tem início nos primeiros 5 minutos (pontualidade)'],
      ['s2_c2', 'Retomada de conhecimentos prévios ou da aula anterior'],
      ['s2_c3', 'Explicação do conteúdo clara, com exemplos adequados'],
      ['s2_c4', 'Variedade metodológica (exposição, grupo, resolução de problemas, etc.)'],
      ['s2_c5', 'Professor faz perguntas para verificar compreensão durante a aula'],
      ['s2_c6', 'Aula tem fechamento/síntese do que foi aprendido'],
    ],
  },
  s3: {
    title: '3. Gestão da Aprendizagem dos Alunos',
    criteria: [
      ['s3_c1', 'Alunos demonstram engajamento e participação ativa'],
      ['s3_c2', 'Professor identifica e atende alunos com dificuldades'],
      ['s3_c3', 'Diferenciação pedagógica (estratégias para diferentes níveis)'],
      ['s3_c4', 'Estratégias de avaliação formativa durante a aula'],
      ['s3_c5', 'Professor dá feedback aos alunos sobre suas produções'],
    ],
  },
  s4: {
    title: '4. Uso de Materiais, Recursos e Tempo',
    criteria: [
      ['s4_c1', 'Utiliza materiais oficiais da SEDUC (cadernos, plataformas, sequências didáticas)'],
      ['s4_c2', 'Uso adequado de recursos disponíveis na escola (tecnologia, laboratório, etc.)'],
      ['s4_c3', 'Tempo da aula bem distribuído entre as atividades'],
      ['s4_c4', 'Registros (quadro, projeção) claros e organizados'],
    ],
  },
  s5: {
    title: '5. Clima, Relações e Postura Profissional',
    criteria: [
      ['s5_c1', 'Ambiente de respeito mútuo e segurança para participação'],
      ['s5_c2', 'Professor mantém boa relação com os alunos (escuta, abertura a dúvidas)'],
      ['s5_c3', 'Manejo adequado de situações de indisciplina ou conflitos'],
      ['s5_c4', 'Professor demonstra preparo prévio e organização dos materiais'],
      ['s5_c5', 'Postura profissional adequada (pontualidade, linguagem, compromisso)'],
    ],
  },
}

export function SectionPanel({ section, state, setRating, toggleMethodology }) {
  const meta = SECTION_META[section]
  return (
    <div>
      <h2 style={{ color: C.accent2, fontSize: 16, marginBottom: 24, fontWeight: 700 }}>
        {meta.title}
      </h2>
      {meta.criteria.map(([field, label]) => (
        <CriteriaRow key={field} label={label} field={field} value={state[field]} onChange={setRating} />
      ))}

      {section === 's2' && (
        <div style={{ marginTop: 24 }}>
          <p style={{ color: C.textMuted, fontSize: 12, marginBottom: 12 }}>
            Estratégias metodológicas observadas:
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {METHODOLOGIES.map(m => {
              const selected = state.s2_methodologies.includes(m)
              return (
                <button
                  key={m}
                  type="button"
                  onClick={() => toggleMethodology(m)}
                  style={{
                    padding: '6px 14px', borderRadius: 20, fontSize: 12, cursor: 'pointer',
                    fontFamily: 'JetBrains Mono', fontWeight: selected ? 600 : 400,
                    background: selected ? C.accent + '33' : C.surface3,
                    border: `1px solid ${selected ? C.accent : C.border}`,
                    color: selected ? C.accent : C.textMuted, transition: 'all 0.15s',
                  }}
                >
                  {m}
                </button>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
