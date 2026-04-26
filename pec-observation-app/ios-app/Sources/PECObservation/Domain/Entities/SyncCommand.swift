import Foundation

public enum SyncCommandType: String, Codable {
    case uploadAudio = "UPLOAD_AUDIO"
    case createObservation = "CREATE_OBSERVATION"
    case updateObservation = "UPDATE_OBSERVATION"
    case createSchool = "CREATE_SCHOOL"
    case createTeacher = "CREATE_TEACHER"
}

public enum SyncStatus: String, Codable {
    case pending = "PENDING"
    case inProgress = "IN_PROGRESS"
    case completed = "COMPLETED"
    case failed = "FAILED"
}

public struct SyncCommand: Identifiable, Codable, Equatable {
    public let commandId: UUID
    public let type: SyncCommandType
    public let payload: [String: String]
    public var status: SyncStatus
    public var retryCount: Int
    public let idempotencyKey: UUID
    public let createdAt: Date
    public var lastAttemptAt: Date?
    public var failureReason: String?

    public var id: UUID { commandId }

    public init(
        commandId: UUID = UUID(),
        type: SyncCommandType,
        payload: [String: String],
        status: SyncStatus = .pending,
        retryCount: Int = 0,
        idempotencyKey: UUID = UUID(),
        createdAt: Date = Date(),
        lastAttemptAt: Date? = nil,
        failureReason: String? = nil
    ) {
        self.commandId = commandId
        self.type = type
        self.payload = payload
        self.status = status
        self.retryCount = retryCount
        self.idempotencyKey = idempotencyKey
        self.createdAt = createdAt
        self.lastAttemptAt = lastAttemptAt
        self.failureReason = failureReason
    }
}
