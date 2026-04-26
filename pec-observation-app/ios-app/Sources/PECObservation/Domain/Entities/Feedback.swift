import Foundation

public enum FeedbackStatus: String, Codable, Equatable {
    case draft = "DRAFT"
    case inReview = "IN_REVIEW"
    case humanReviewed = "HUMAN_REVIEWED"
    case approved = "APPROVED"

    public var displayName: String {
        switch self {
        case .draft: return "Rascunho IA"
        case .inReview: return "Em Revisão"
        case .humanReviewed: return "Revisado"
        case .approved: return "Aprovado"
        }
    }
}

public struct FeedbackItem: Codable, Equatable {
    public var title: String
    public var description: String
    public var evidence: String?

    public init(title: String, description: String, evidence: String? = nil) {
        self.title = title
        self.description = description
        self.evidence = evidence
    }
}

public struct ActionItem: Identifiable, Codable, Equatable {
    public let id: UUID
    public var description: String
    public var owner: String
    public var dueDate: String?
    public var expectedEvidence: String?
    public var isCompleted: Bool

    public init(id: UUID = UUID(), description: String, owner: String = "Professor",
                dueDate: String? = nil, expectedEvidence: String? = nil,
                isCompleted: Bool = false) {
        self.id = id
        self.description = description
        self.owner = owner
        self.dueDate = dueDate
        self.expectedEvidence = expectedEvidence
        self.isCompleted = isCompleted
    }
}

public struct Feedback: Identifiable, Codable, Equatable {
    public let id: UUID
    public let observationId: UUID
    public var summary: String?
    public var strengths: [FeedbackItem]
    public var improvementPoints: [FeedbackItem]
    public var actionItems: [ActionItem]
    public var status: FeedbackStatus
    public var version: Int
    public var reviewedAt: Date?

    public init(id: UUID = UUID(), observationId: UUID, summary: String? = nil,
                strengths: [FeedbackItem] = [], improvementPoints: [FeedbackItem] = [],
                actionItems: [ActionItem] = [], status: FeedbackStatus = .draft,
                version: Int = 1, reviewedAt: Date? = nil) {
        self.id = id
        self.observationId = observationId
        self.summary = summary
        self.strengths = strengths
        self.improvementPoints = improvementPoints
        self.actionItems = actionItems
        self.status = status
        self.version = version
        self.reviewedAt = reviewedAt
    }
}
