import Foundation

public enum ObservationStatus: String, Codable, CaseIterable, Equatable {
    case draft = "DRAFT"
    case readyToRecord = "READY_TO_RECORD"
    case recorded = "RECORDED"
    case audioUploaded = "AUDIO_UPLOADED"
    case transcribing = "TRANSCRIBING"
    case transcribed = "TRANSCRIBED"
    case generatingFeedback = "GENERATING_FEEDBACK"
    case feedbackReady = "FEEDBACK_READY"
    case inReview = "IN_REVIEW"
    case humanReviewed = "HUMAN_REVIEWED"
    case approved = "APPROVED"

    public var displayName: String {
        switch self {
        case .draft: return "Rascunho"
        case .readyToRecord: return "Pronto para Gravar"
        case .recorded: return "Gravado"
        case .audioUploaded: return "Áudio Enviado"
        case .transcribing: return "Transcrevendo"
        case .transcribed: return "Transcrito"
        case .generatingFeedback: return "Gerando Feedback"
        case .feedbackReady: return "Feedback Disponível"
        case .inReview: return "Em Revisão"
        case .humanReviewed: return "Revisado"
        case .approved: return "Aprovado"
        }
    }
}

public struct AudioRecordingResult: Codable, Equatable {
    public let observationId: UUID
    public let localFileUrl: URL
    public let durationSeconds: Int
    public let fileSizeBytes: Int
    public let checksum: String
    public let codec: String

    public init(observationId: UUID, localFileUrl: URL, durationSeconds: Int,
                fileSizeBytes: Int, checksum: String, codec: String = "aac") {
        self.observationId = observationId
        self.localFileUrl = localFileUrl
        self.durationSeconds = durationSeconds
        self.fileSizeBytes = fileSizeBytes
        self.checksum = checksum
        self.codec = codec
    }
}

public struct Observation: Identifiable, Equatable, Codable {
    public let id: UUID
    public let schoolId: UUID
    public let teacherId: UUID
    public var subject: String
    public var grade: String
    public var lessonTheme: String
    public var lessonObjectives: String
    public var status: ObservationStatus
    public var audioRecording: AudioRecordingResult?
    public var transcription: String?
    public let createdAt: Date
    public var updatedAt: Date

    public init(
        id: UUID = UUID(),
        schoolId: UUID,
        teacherId: UUID,
        subject: String,
        grade: String,
        lessonTheme: String,
        lessonObjectives: String = "",
        status: ObservationStatus = .draft,
        audioRecording: AudioRecordingResult? = nil,
        transcription: String? = nil,
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.schoolId = schoolId
        self.teacherId = teacherId
        self.subject = subject
        self.grade = grade
        self.lessonTheme = lessonTheme
        self.lessonObjectives = lessonObjectives
        self.status = status
        self.audioRecording = audioRecording
        self.transcription = transcription
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }

    public var isReadyForRecording: Bool {
        !subject.isEmpty && !grade.isEmpty && !lessonTheme.isEmpty
    }
}
