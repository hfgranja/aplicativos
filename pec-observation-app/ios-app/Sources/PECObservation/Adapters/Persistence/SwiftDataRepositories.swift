#if os(iOS)
import Foundation
import SwiftData

public final class SwiftDataObservationRepository: ObservationRepositoryPort {
    private let context: ModelContext

    public init(context: ModelContext) {
        self.context = context
    }

    public func save(_ observation: Observation) throws {
        let descriptor = FetchDescriptor<ObservationEntity>(
            predicate: #Predicate { $0.id == observation.id }
        )
        if let existing = try context.fetch(descriptor).first {
            existing.statusRaw = observation.status.rawValue
            existing.audioLocalPath = observation.audioRecording?.localFileUrl.absoluteString
            existing.audioDurationSeconds = observation.audioRecording?.durationSeconds
            existing.audioFileSizeBytes = observation.audioRecording?.fileSizeBytes
            existing.audioChecksum = observation.audioRecording?.checksum
            existing.audioCodec = observation.audioRecording?.codec
            existing.transcription = observation.transcription
            existing.updatedAt = observation.updatedAt
        } else {
            context.insert(ObservationEntity(from: observation))
        }
        try context.save()
    }

    public func fetchAll() throws -> [Observation] {
        let descriptor = FetchDescriptor<ObservationEntity>(
            sortBy: [SortDescriptor(\.createdAt, order: .reverse)]
        )
        return try context.fetch(descriptor).map { $0.toDomain() }
    }

    public func fetchById(_ id: UUID) throws -> Observation? {
        let descriptor = FetchDescriptor<ObservationEntity>(
            predicate: #Predicate { $0.id == id }
        )
        return try context.fetch(descriptor).first?.toDomain()
    }

    public func fetchByStatus(_ status: ObservationStatus) throws -> [Observation] {
        let raw = status.rawValue
        let descriptor = FetchDescriptor<ObservationEntity>(
            predicate: #Predicate { $0.statusRaw == raw }
        )
        return try context.fetch(descriptor).map { $0.toDomain() }
    }

    public func delete(_ id: UUID) throws {
        let descriptor = FetchDescriptor<ObservationEntity>(
            predicate: #Predicate { $0.id == id }
        )
        if let entity = try context.fetch(descriptor).first {
            context.delete(entity)
            try context.save()
        }
    }
}

public final class SwiftDataSyncQueue: SyncQueuePort {
    private let context: ModelContext

    public init(context: ModelContext) {
        self.context = context
    }

    public func enqueue(_ command: SyncCommand) throws {
        context.insert(SyncCommandEntity(from: command))
        try context.save()
    }

    public func pendingCommands() throws -> [SyncCommand] {
        let descriptor = FetchDescriptor<SyncCommandEntity>(
            predicate: #Predicate { $0.statusRaw == "PENDING" },
            sortBy: [SortDescriptor(\.createdAt)]
        )
        return try context.fetch(descriptor).map { $0.toDomain() }
    }

    public func markInProgress(_ commandId: UUID) throws {
        try _updateStatus(commandId, status: "IN_PROGRESS")
    }

    public func markCompleted(_ commandId: UUID) throws {
        try _updateStatus(commandId, status: "COMPLETED")
    }

    public func markFailed(_ commandId: UUID, reason: String) throws {
        let descriptor = FetchDescriptor<SyncCommandEntity>(
            predicate: #Predicate { $0.commandId == commandId }
        )
        if let entity = try context.fetch(descriptor).first {
            entity.statusRaw = "PENDING"  // Re-queue for retry
            entity.retryCount += 1
            entity.lastAttemptAt = Date()
            entity.failureReason = reason
            try context.save()
        }
    }

    public func pendingCount() throws -> Int {
        let descriptor = FetchDescriptor<SyncCommandEntity>(
            predicate: #Predicate { $0.statusRaw == "PENDING" }
        )
        return try context.fetchCount(descriptor)
    }

    private func _updateStatus(_ commandId: UUID, status: String) throws {
        let descriptor = FetchDescriptor<SyncCommandEntity>(
            predicate: #Predicate { $0.commandId == commandId }
        )
        if let entity = try context.fetch(descriptor).first {
            entity.statusRaw = status
            entity.lastAttemptAt = Date()
            try context.save()
        }
    }
}
#endif
