#if os(iOS)
import Foundation
import SwiftData

@Model
public final class ObservationEntity {
    @Attribute(.unique) public var id: UUID
    public var schoolId: UUID
    public var teacherId: UUID
    public var subject: String
    public var grade: String
    public var lessonTheme: String
    public var lessonObjectives: String
    public var statusRaw: String
    public var audioLocalPath: String?
    public var audioDurationSeconds: Int?
    public var audioFileSizeBytes: Int?
    public var audioChecksum: String?
    public var audioCodec: String?
    public var transcription: String?
    public var createdAt: Date
    public var updatedAt: Date

    public init(from obs: Observation) {
        self.id = obs.id
        self.schoolId = obs.schoolId
        self.teacherId = obs.teacherId
        self.subject = obs.subject
        self.grade = obs.grade
        self.lessonTheme = obs.lessonTheme
        self.lessonObjectives = obs.lessonObjectives
        self.statusRaw = obs.status.rawValue
        self.audioLocalPath = obs.audioRecording?.localFileUrl.absoluteString
        self.audioDurationSeconds = obs.audioRecording?.durationSeconds
        self.audioFileSizeBytes = obs.audioRecording?.fileSizeBytes
        self.audioChecksum = obs.audioRecording?.checksum
        self.audioCodec = obs.audioRecording?.codec
        self.transcription = obs.transcription
        self.createdAt = obs.createdAt
        self.updatedAt = obs.updatedAt
    }

    public func toDomain() -> Observation {
        var recording: AudioRecordingResult?
        if let path = audioLocalPath,
           let url = URL(string: path),
           let checksum = audioChecksum,
           let codec = audioCodec {
            recording = AudioRecordingResult(
                observationId: id,
                localFileUrl: url,
                durationSeconds: audioDurationSeconds ?? 0,
                fileSizeBytes: audioFileSizeBytes ?? 0,
                checksum: checksum,
                codec: codec
            )
        }
        return Observation(
            id: id, schoolId: schoolId, teacherId: teacherId,
            subject: subject, grade: grade, lessonTheme: lessonTheme,
            lessonObjectives: lessonObjectives,
            status: ObservationStatus(rawValue: statusRaw) ?? .draft,
            audioRecording: recording,
            transcription: transcription,
            createdAt: createdAt, updatedAt: updatedAt
        )
    }
}

@Model
public final class SyncCommandEntity {
    @Attribute(.unique) public var commandId: UUID
    public var typeRaw: String
    public var payloadJSON: String
    public var statusRaw: String
    public var retryCount: Int
    public var idempotencyKey: UUID
    public var createdAt: Date
    public var lastAttemptAt: Date?
    public var failureReason: String?

    public init(from cmd: SyncCommand) {
        self.commandId = cmd.commandId
        self.typeRaw = cmd.type.rawValue
        self.payloadJSON = (try? String(data: JSONEncoder().encode(cmd.payload),
                                        encoding: .utf8)) ?? "{}"
        self.statusRaw = cmd.status.rawValue
        self.retryCount = cmd.retryCount
        self.idempotencyKey = cmd.idempotencyKey
        self.createdAt = cmd.createdAt
        self.lastAttemptAt = cmd.lastAttemptAt
        self.failureReason = cmd.failureReason
    }

    public func toDomain() -> SyncCommand {
        let payload = (try? JSONDecoder().decode([String: String].self,
                        from: Data(payloadJSON.utf8))) ?? [:]
        return SyncCommand(
            commandId: commandId,
            type: SyncCommandType(rawValue: typeRaw) ?? .createObservation,
            payload: payload,
            status: SyncStatus(rawValue: statusRaw) ?? .pending,
            retryCount: retryCount,
            idempotencyKey: idempotencyKey,
            createdAt: createdAt,
            lastAttemptAt: lastAttemptAt,
            failureReason: failureReason
        )
    }
}
#endif
