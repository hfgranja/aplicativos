import Foundation

public enum DocumentType: String, Codable, CaseIterable {
    case seducPolicy      = "seduc_policy"
    case curriculumGuide  = "curriculum_guide"
    case evaluationRubric = "evaluation_rubric"
    case feedbackExample  = "feedback_example"
    case other            = "other"

    public var displayName: String {
        switch self {
        case .seducPolicy:      return "Política SEDUC"
        case .curriculumGuide:  return "Guia Curricular"
        case .evaluationRubric: return "Rubrica de Avaliação"
        case .feedbackExample:  return "Exemplo de Feedback"
        case .other:            return "Outro"
        }
    }
}

public struct KnowledgeDocument: Identifiable, Codable, Equatable {
    public let id: String
    public let title: String
    public let documentType: String
    public let sourceFilename: String
    public let description: String?
    public let chunkCount: Int
    public let uploadedBy: String
    public let isActive: Bool
    public let createdAt: String

    public var documentTypeDisplay: String {
        DocumentType(rawValue: documentType)?.displayName ?? documentType
    }

    enum CodingKeys: String, CodingKey {
        case id, title, description, isActive = "is_active", createdAt = "created_at"
        case documentType = "document_type", sourceFilename = "source_filename"
        case chunkCount = "chunk_count", uploadedBy = "uploaded_by"
    }
}
