import Foundation

public enum StyleTone: String, Codable, CaseIterable {
    case formal       = "formal"
    case constructive = "constructive"
    case direct       = "direct"
    case supportive   = "supportive"

    public var displayName: String {
        switch self {
        case .formal:       return "Formal"
        case .constructive: return "Construtivo"
        case .direct:       return "Direto"
        case .supportive:   return "Acolhedor"
        }
    }
}

public struct FeedbackStyle: Identifiable, Codable, Equatable {
    public let id: String
    public let name: String
    public let description: String
    public let tone: String
    public let templatePrompt: String
    public let exampleStrengths: [String]
    public let exampleImprovements: [String]
    public let isActive: Bool
    public let isDefault: Bool
    public let createdAt: String

    public var toneDisplay: String {
        StyleTone(rawValue: tone)?.displayName ?? tone
    }

    enum CodingKeys: String, CodingKey {
        case id, name, description, tone, isActive = "is_active"
        case isDefault = "is_default", createdAt = "created_at"
        case templatePrompt = "template_prompt"
        case exampleStrengths = "example_strengths"
        case exampleImprovements = "example_improvements"
    }
}
