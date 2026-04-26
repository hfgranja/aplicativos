import Foundation

public enum RecordingState: String, Equatable {
    case idle
    case preparing
    case recording
    case paused
    case stopping
    case completed
    case failed
}

// Exact protocol from SDD section 13.3
public protocol AudioRecordingPort {
    func requestPermission() async -> Bool
    func startRecording(observationId: UUID) async throws
    func pauseRecording() async throws
    func resumeRecording() async throws
    func stopRecording() async throws -> AudioRecordingResult
    var currentState: RecordingState { get }
    var elapsedSeconds: Int { get }
}
