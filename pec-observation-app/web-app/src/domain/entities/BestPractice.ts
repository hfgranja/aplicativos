export type PracticeStatus = 'draft' | 'published' | 'archived'

export type PedagogicalCriterion =
  | 'planejamento' | 'didatica' | 'engajamento' | 'avaliacao' | 'gestao'

export const CRITERION_LABELS: Record<PedagogicalCriterion, string> = {
  planejamento: 'Planejamento Curricular',
  didatica:     'Clareza Didática',
  engajamento:  'Engajamento',
  avaliacao:    'Avaliação Formativa',
  gestao:       'Gestão do Tempo',
}

export const CRITERION_EMOJI: Record<PedagogicalCriterion, string> = {
  planejamento: '📐',
  didatica:     '🎯',
  engajamento:  '🙋',
  avaliacao:    '📊',
  gestao:       '⏱️',
}

export interface BestPracticeCard {
  id:              string
  title:           string
  criterion:       PedagogicalCriterion
  subject:         string
  grade:           string
  excerpt:         string
  aiExplanation:   string
  rubricAlignment: string[]
  tags:            string[]
  status:          PracticeStatus
  hasAudio:        boolean
  audioUrl?:       string
  createdAt:       string
  publishedAt?:    string
}

export interface PracticeDistribution {
  distributionId: string
  card:           BestPracticeCard
  message:        string
  sentAt:         string
  viewedAt?:      string
}
