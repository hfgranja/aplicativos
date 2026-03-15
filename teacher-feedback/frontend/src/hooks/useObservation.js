import { useReducer } from 'react'

export const STEPS = [
  { id: 'upload', label: 'Upload & Dados' },
  { id: 's1', label: 'Seção 1 – Planejamento' },
  { id: 's2', label: 'Seção 2 – Condução Didática' },
  { id: 's3', label: 'Seção 3 – Aprendizagem' },
  { id: 's4', label: 'Seção 4 – Materiais' },
  { id: 's5', label: 'Seção 5 – Clima' },
  { id: 'narrative', label: 'Narrativa PEC' },
  { id: 'teacher_questions', label: 'Perguntas ao Professor' },
  { id: 'references', label: 'Referências' },
  { id: 'review', label: 'Revisão' },
]

const initialState = {
  step: 0,
  // Upload & basic info
  teacher_id: '',
  media_file_id: null,
  observed_at: new Date().toISOString().slice(0, 16),
  pec_name: '',
  focus_area: '',
  // Section 1
  s1_c1: null, s1_c2: null, s1_c3: null, s1_c4: null,
  // Section 2
  s2_c1: null, s2_c2: null, s2_c3: null, s2_c4: null, s2_c5: null, s2_c6: null,
  s2_methodologies: [],
  // Section 3
  s3_c1: null, s3_c2: null, s3_c3: null, s3_c4: null, s3_c5: null,
  // Section 4
  s4_c1: null, s4_c2: null, s4_c3: null, s4_c4: null,
  // Section 5
  s5_c1: null, s5_c2: null, s5_c3: null, s5_c4: null, s5_c5: null,
  // Narrative
  habilidades_curriculo: '',
  pontos_fortes: ['', '', ''],
  focos_desenvolvimento: ['', '', ''],
  sugestoes: '',
  // Teacher questions
  teacher_feeling: '',
  teacher_comments: '',
  teacher_expectations: '',
  teacher_commitment: '',
  // References
  bncc_skills: [],
  bncc_input: '',
  seduc_materials: '',
  next_observation_date: '',
  next_observation_focus: '',
  combined_actions: [],
}

function reducer(state, action) {
  switch (action.type) {
    case 'SET': return { ...state, [action.field]: action.value }
    case 'SET_RATING': return { ...state, [action.field]: action.value }
    case 'TOGGLE_METHODOLOGY': {
      const m = state.s2_methodologies
      return {
        ...state,
        s2_methodologies: m.includes(action.value)
          ? m.filter(x => x !== action.value)
          : [...m, action.value],
      }
    }
    case 'SET_ARRAY_ITEM': {
      const arr = [...state[action.field]]
      arr[action.index] = action.value
      return { ...state, [action.field]: arr }
    }
    case 'ADD_BNCC_SKILL': {
      const skill = state.bncc_input.trim().toUpperCase()
      if (!skill || state.bncc_skills.includes(skill)) return { ...state, bncc_input: '' }
      return { ...state, bncc_skills: [...state.bncc_skills, skill], bncc_input: '' }
    }
    case 'REMOVE_BNCC_SKILL': return {
      ...state, bncc_skills: state.bncc_skills.filter(s => s !== action.value)
    }
    case 'ADD_ACTION': return {
      ...state,
      combined_actions: [...state.combined_actions, { action: '', responsible: 'professor', deadline: '' }],
    }
    case 'SET_ACTION': {
      const actions = [...state.combined_actions]
      actions[action.index] = { ...actions[action.index], [action.field]: action.value }
      return { ...state, combined_actions: actions }
    }
    case 'REMOVE_ACTION': return {
      ...state, combined_actions: state.combined_actions.filter((_, i) => i !== action.index)
    }
    case 'NEXT': return { ...state, step: Math.min(state.step + 1, STEPS.length - 1) }
    case 'PREV': return { ...state, step: Math.max(state.step - 1, 0) }
    case 'GO_TO': return { ...state, step: action.step }
    case 'RESET': return { ...initialState }
    default: return state
  }
}

export function useObservation() {
  const [state, dispatch] = useReducer(reducer, initialState)

  const set = (field, value) => dispatch({ type: 'SET', field, value })
  const setRating = (field, value) => dispatch({ type: 'SET_RATING', field, value })
  const toggleMethodology = (value) => dispatch({ type: 'TOGGLE_METHODOLOGY', value })
  const setArrayItem = (field, index, value) => dispatch({ type: 'SET_ARRAY_ITEM', field, index, value })
  const addBnccSkill = () => dispatch({ type: 'ADD_BNCC_SKILL' })
  const removeBnccSkill = (value) => dispatch({ type: 'REMOVE_BNCC_SKILL', value })
  const addAction = () => dispatch({ type: 'ADD_ACTION' })
  const setAction = (index, field, value) => dispatch({ type: 'SET_ACTION', index, field, value })
  const removeAction = (index) => dispatch({ type: 'REMOVE_ACTION', index })
  const next = () => dispatch({ type: 'NEXT' })
  const prev = () => dispatch({ type: 'PREV' })
  const goTo = (step) => dispatch({ type: 'GO_TO', step })
  const reset = () => dispatch({ type: 'RESET' })

  const toPayload = () => ({
    teacher_id: state.teacher_id,
    media_file_id: state.media_file_id || null,
    observed_at: state.observed_at,
    pec_name: state.pec_name,
    focus_area: state.focus_area,
    s1_c1: state.s1_c1, s1_c2: state.s1_c2, s1_c3: state.s1_c3, s1_c4: state.s1_c4,
    s2_c1: state.s2_c1, s2_c2: state.s2_c2, s2_c3: state.s2_c3,
    s2_c4: state.s2_c4, s2_c5: state.s2_c5, s2_c6: state.s2_c6,
    s2_methodologies: JSON.stringify(state.s2_methodologies),
    s3_c1: state.s3_c1, s3_c2: state.s3_c2, s3_c3: state.s3_c3, s3_c4: state.s3_c4, s3_c5: state.s3_c5,
    s4_c1: state.s4_c1, s4_c2: state.s4_c2, s4_c3: state.s4_c3, s4_c4: state.s4_c4,
    s5_c1: state.s5_c1, s5_c2: state.s5_c2, s5_c3: state.s5_c3, s5_c4: state.s5_c4, s5_c5: state.s5_c5,
    habilidades_curriculo: state.habilidades_curriculo,
    pontos_fortes: JSON.stringify(state.pontos_fortes.filter(Boolean)),
    focos_desenvolvimento: JSON.stringify(state.focos_desenvolvimento.filter(Boolean)),
    sugestoes: state.sugestoes,
    teacher_feeling: state.teacher_feeling,
    teacher_comments: state.teacher_comments,
    teacher_expectations: state.teacher_expectations,
    teacher_commitment: state.teacher_commitment,
    bncc_skills: JSON.stringify(state.bncc_skills),
    seduc_materials: state.seduc_materials,
    next_observation_date: state.next_observation_date || null,
    next_observation_focus: state.next_observation_focus,
    combined_actions: JSON.stringify(state.combined_actions),
  })

  return { state, set, setRating, toggleMethodology, setArrayItem, addBnccSkill, removeBnccSkill, addAction, setAction, removeAction, next, prev, goTo, reset, toPayload }
}
