import Foundation

public enum PracticeStatus: String, Codable {
    case draft     = "draft"
    case published = "published"
    case archived  = "archived"
}

public enum PedagogicalCriterion: String, Codable, CaseIterable {
    case planejamento = "planejamento"
    case didatica     = "didatica"
    case engajamento  = "engajamento"
    case avaliacao    = "avaliacao"
    case gestao       = "gestao"

    public var displayName: String {
        switch self {
        case .planejamento: return "Planejamento Curricular"
        case .didatica:     return "Clareza Didática"
        case .engajamento:  return "Engajamento"
        case .avaliacao:    return "Avaliação Formativa"
        case .gestao:       return "Gestão do Tempo"
        }
    }

    public var emoji: String {
        switch self {
        case .planejamento: return "📐"
        case .didatica:     return "🎯"
        case .engajamento:  return "🙋"
        case .avaliacao:    return "📊"
        case .gestao:       return "⏱️"
        }
    }
}

public struct BestPracticeCard: Identifiable, Codable, Equatable {
    public let id:             String
    public let title:          String
    public let criterion:      String
    public let subject:        String
    public let grade:          String
    public let excerpt:        String
    public let aiExplanation:  String
    public let rubricAlignment: [String]
    public let tags:           [String]
    public let status:         String
    public let hasAudio:       Bool
    public let audioUrl:       String?
    public let createdAt:      String
    public let publishedAt:    String?

    public var criterionEnum: PedagogicalCriterion? {
        PedagogicalCriterion(rawValue: criterion)
    }

    enum CodingKeys: String, CodingKey {
        case id, title, criterion, subject, grade, excerpt, tags, status
        case aiExplanation  = "ai_explanation"
        case rubricAlignment = "rubric_alignment"
        case hasAudio       = "has_audio"
        case audioUrl       = "audio_url"
        case createdAt      = "created_at"
        case publishedAt    = "published_at"
    }
}

public struct Distribution: Identifiable, Codable {
    public let id:             String
    public let card:           BestPracticeCard
    public let message:        String
    public let sentAt:         String
    public let viewedAt:       String?

    enum CodingKeys: String, CodingKey {
        case id, card, message
        case sentAt   = "sent_at"
        case viewedAt = "viewed_at"
    }
}
