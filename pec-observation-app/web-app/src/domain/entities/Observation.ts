export type ObservationStatus =
  | 'draft'
  | 'ready_to_record'
  | 'recorded'
  | 'audio_uploaded'
  | 'transcribing'
  | 'transcribed'
  | 'generating_feedback'
  | 'feedback_ready'
  | 'in_review'
  | 'human_reviewed'
  | 'approved'

export interface Observation {
  id: string
  schoolId: string
  teacherId: string
  pecId: string
  subject: string
  grade: string
  scheduledAt: string
  durationMinutes: number
  status: ObservationStatus
  notes?: string
  feedbackStyleId?: string
  createdAt: string
  updatedAt: string
  schoolName?: string
  teacherName?: string
}

export const STATUS_LABELS: Record<ObservationStatus, string> = {
  draft:               'Rascunho',
  ready_to_record:     'Pronto para gravar',
  recorded:            'Gravado',
  audio_uploaded:      'Áudio enviado',
  transcribing:        'Transcrevendo',
  transcribed:         'Transcrito',
  generating_feedback: 'Gerando feedback',
  feedback_ready:      'Feedback pronto',
  in_review:           'Em revisão',
  human_reviewed:      'Revisado',
  approved:            'Aprovado',
}

export const STATUS_COLOR: Record<ObservationStatus, string> = {
  draft:               'badge-gray',
  ready_to_record:     'badge-blue',
  recorded:            'badge-blue',
  audio_uploaded:      'badge-blue',
  transcribing:        'badge-yellow',
  transcribed:         'badge-yellow',
  generating_feedback: 'badge-yellow',
  feedback_ready:      'badge-green',
  in_review:           'badge-yellow',
  human_reviewed:      'badge-green',
  approved:            'badge-green',
}
