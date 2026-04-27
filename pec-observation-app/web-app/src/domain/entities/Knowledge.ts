export type DocumentType =
  | 'seduc_policy'
  | 'curriculum_guide'
  | 'evaluation_rubric'
  | 'feedback_example'
  | 'other'

export const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  seduc_policy:      'Política SEDUC',
  curriculum_guide:  'Guia Curricular',
  evaluation_rubric: 'Rubrica de Avaliação',
  feedback_example:  'Exemplo de Feedback',
  other:             'Outro',
}

export interface KnowledgeDocument {
  id: string
  title: string
  documentType: DocumentType
  sourceFilename: string
  description?: string
  chunkCount: number
  uploadedBy: string
  isActive: boolean
  createdAt: string
}

export type StyleTone = 'formal' | 'constructive' | 'direct' | 'supportive'

export const STYLE_TONE_LABELS: Record<StyleTone, string> = {
  formal:       'Formal',
  constructive: 'Construtivo',
  direct:       'Direto',
  supportive:   'Encorajador',
}

export interface FeedbackStyle {
  id: string
  name: string
  description: string
  tone: StyleTone
  templatePrompt: string
  exampleStrengths: string[]
  exampleImprovements: string[]
  isActive: boolean
  isDefault: boolean
  createdAt: string
}
