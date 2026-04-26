import Foundation

public struct PresignedURLResponse: Decodable {
    public let uploadId: String
    public let uploadUrl: String
    public let expiresAt: String
}

public struct ConfirmUploadResponse: Decodable {
    public let uploadId: String
    public let status: String
}

public final class SyncUseCase {
    private let syncQueue: SyncQueuePort
    private let network: NetworkClientPort
    private let token: () -> String?
    private let maxRetries = 5

    public init(syncQueue: SyncQueuePort, network: NetworkClientPort, token: @escaping () -> String?) {
        self.syncQueue = syncQueue
        self.network = network
        self.token = token
    }

    public func processPendingCommands() async {
        let commands: [SyncCommand]
        do {
            commands = try syncQueue.pendingCommands()
        } catch {
            return
        }

        for command in commands {
            guard command.retryCount < maxRetries else {
                try? syncQueue.markFailed(command.commandId, reason: "Max retries exceeded")
                continue
            }
            do {
                try? syncQueue.markInProgress(command.commandId)
                try await processCommand(command)
                try? syncQueue.markCompleted(command.commandId)
            } catch {
                let delay = pow(2.0, Double(command.retryCount)) // 1, 2, 4, 8, 16 seconds
                try? syncQueue.markFailed(command.commandId,
                                          reason: error.localizedDescription)
                try? await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
            }
        }
    }

    private func processCommand(_ command: SyncCommand) async throws {
        switch command.type {
        case .uploadAudio:
            try await processAudioUpload(command)
        case .createObservation, .updateObservation, .createSchool, .createTeacher:
            // These are handled via direct API calls in the view models;
            // sync queue is used for retry if offline
            break
        }
    }

    private func processAudioUpload(_ command: SyncCommand) async throws {
        guard let observationId = command.payload["observationId"],
              let audioLocalPath = command.payload["audioLocalPath"],
              let audioURL = URL(string: audioLocalPath) else {
            throw DomainError.validationFailed("Invalid upload audio command payload")
        }

        let audioData = try Data(contentsOf: audioURL)
        let fileSize = command.payload["fileSizeBytes"].flatMap { Int($0) } ?? audioData.count
        let checksum = command.payload["checksum"] ?? ""
        let codec = command.payload["codec"] ?? "aac"
        let duration = command.payload["durationSeconds"].flatMap { Int($0) } ?? 0

        let presignedBody = [
            "observation_id": observationId,
            "file_name": "observation-\(observationId).m4a",
            "file_size_bytes": fileSize,
            "checksum": checksum,
            "codec": codec,
            "idempotency_key": command.idempotencyKey.uuidString,
        ] as [String: Any]

        let presignedResponse: PresignedURLResponse = try await network.post(
            path: "/api/v1/audio/presigned-url",
            body: AnyEncodable(presignedBody),
            token: token()
        )

        guard let uploadURL = URL(string: presignedResponse.uploadUrl) else {
            throw NetworkError.decodingFailed("Invalid presigned URL")
        }
        try await network.put(url: uploadURL, data: audioData, contentType: "audio/mp4")

        let _: ConfirmUploadResponse = try await network.post(
            path: "/api/v1/audio/confirm/\(presignedResponse.uploadId)",
            body: ["duration_seconds": duration],
            token: token()
        )
    }
}

// Helper to encode arbitrary dictionaries
struct AnyEncodable: Encodable {
    private let _encode: (Encoder) throws -> Void

    init(_ value: [String: Any]) {
        self._encode = { encoder in
            var container = encoder.singleValueContainer()
            let jsonData = try JSONSerialization.data(withJSONObject: value)
            let decoded = try JSONDecoder().decode(AnyCodable.self, from: jsonData)
            try container.encode(decoded)
        }
    }

    func encode(to encoder: Encoder) throws {
        try _encode(encoder)
    }
}

private struct AnyCodable: Codable {
    private var value: Any

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let v = try? container.decode([String: AnyCodable].self) {
            value = v
        } else if let v = try? container.decode([AnyCodable].self) {
            value = v
        } else if let v = try? container.decode(String.self) {
            value = v
        } else if let v = try? container.decode(Int.self) {
            value = v
        } else if let v = try? container.decode(Double.self) {
            value = v
        } else if let v = try? container.decode(Bool.self) {
            value = v
        } else {
            value = ""
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch value {
        case let v as [String: AnyCodable]:
            try container.encode(v)
        case let v as [AnyCodable]:
            try container.encode(v)
        case let v as String:
            try container.encode(v)
        case let v as Int:
            try container.encode(v)
        case let v as Double:
            try container.encode(v)
        case let v as Bool:
            try container.encode(v)
        default:
            try container.encodeNil()
        }
    }
}
