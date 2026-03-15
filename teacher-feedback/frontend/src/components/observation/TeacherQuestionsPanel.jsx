import { C } from '../../colors'
import { Textarea } from '../shared'

export function TeacherQuestionsPanel({ state, set }) {
  return (
    <div>
      <h2 style={{ color: C.accent2, fontSize: 16, marginBottom: 8, fontWeight: 700 }}>
        Perguntas ao Professor
      </h2>
      <p style={{ color: C.textMuted, fontSize: 13, marginBottom: 24, lineHeight: 1.6 }}>
        Registre as respostas do professor durante a devolutiva formativa.
        Estas informações ajudarão o LLM a personalizar o feedback com base na perspectiva do professor.
      </p>

      <Textarea
        label="Como você se sentiu durante a aula observada?"
        value={state.teacher_feeling}
        onChange={v => set('teacher_feeling', v)}
        rows={3}
        placeholder="Registre como o professor descreveu seus sentimentos sobre a aula..."
      />

      <Textarea
        label="Há algo que gostaria de comentar sobre a aula antes de conversarmos sobre a observação?"
        value={state.teacher_comments}
        onChange={v => set('teacher_comments', v)}
        rows={3}
        placeholder="Comentários livres do professor..."
      />

      <Textarea
        label="Quais foram suas expectativas em relação aos objetivos da aula? Você considera que foram alcançados?"
        value={state.teacher_expectations}
        onChange={v => set('teacher_expectations', v)}
        rows={3}
        placeholder="Percepção do professor sobre os objetivos e resultados..."
      />

      <Textarea
        label="O que você se compromete a colocar em prática a partir desta conversa?"
        value={state.teacher_commitment}
        onChange={v => set('teacher_commitment', v)}
        rows={3}
        placeholder="Comprometimentos e metas do professor..."
      />
    </div>
  )
}
