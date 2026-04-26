import Foundation

public final class RecordAudioUseCase {
    private let recorder: AudioRecordingPort
    private let repo: ObservationRepositoryPort
    private let syncQueue: SyncQueuePort

    public init(recorder: AudioRecordingPort, repo: ObservationRepositoryPort,
                syncQueue: SyncQueuePort) {
        self.recorder = recorder
        self.repo = repo
        self.syncQueue = syncQueue
    }

    public func startRecording(for observationId: UUID) async throws {
        guard var obs = try repo.fetchById(observationId) else {
            throw DomainError.notFound("Observation")
        }
        guard obs.isReadyForRecording else {
            throw DomainError.validationFailed("Preencha escola, professor, componente, série e tema antes de gravar")
        }

        let permitted = await recorder.requestPermission()
        guard permitted else { throw RecordingError.permissionDenied }

        obs.status = .readyToRecord
        try repo.save(obs)
        try await recorder.startRecording(observationId: observationId)
    }

    public func pauseRecording() async throws {
        try await recorder.pauseRecording()
    }

    public func resumeRecording() async throws {
        try await recorder.resumeRecording()
    }

    public func stopRecording(for observationId: UUID) async throws -> AudioRecordingResult {
        let result = try await recorder.stopRecording()

        guard var obs = try repo.fetchById(observationId) else {
            throw DomainError.notFound("Observation")
        }
        obs.audioRecording = result
        obs.status = .recorded
        obs.updatedAt = Date()
        try repo.save(obs)

        let command = SyncCommand(
            type: .uploadAudio,
            payload: [
                "observationId": observationId.uuidString,
                "audioLocalPath": result.localFileUrl.absoluteString,
                "checksum": result.checksum,
                "codec": result.codec,
                "durationSeconds": String(result.durationSeconds),
                "fileSizeBytes": String(result.fileSizeBytes),
            ]
        )
        try syncQueue.enqueue(command)
        return result
    }
}
