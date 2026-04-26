#if os(iOS)
import Foundation
import Observation

@Observable
public final class RecordingViewModel {
    private let recordAudioUseCase: RecordAudioUseCase
    public var recordingState: RecordingState = .idle
    public var elapsedSeconds: Int = 0
    public var errorMessage: String?
    public var lastResult: AudioRecordingResult?

    public var formattedTime: String {
        let minutes = elapsedSeconds / 60
        let seconds = elapsedSeconds % 60
        return String(format: "%02d:%02d", minutes, seconds)
    }

    public init(recordAudioUseCase: RecordAudioUseCase) {
        self.recordAudioUseCase = recordAudioUseCase
    }

    public func startRecording(observationId: UUID) async {
        errorMessage = nil
        do {
            try await recordAudioUseCase.startRecording(for: observationId)
            recordingState = .recording
        } catch {
            recordingState = .failed
            errorMessage = error.localizedDescription
        }
    }

    public func pauseRecording() async {
        do {
            try await recordAudioUseCase.pauseRecording()
            recordingState = .paused
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    public func resumeRecording() async {
        do {
            try await recordAudioUseCase.resumeRecording()
            recordingState = .recording
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    public func stopRecording(observationId: UUID) async {
        recordingState = .stopping
        do {
            lastResult = try await recordAudioUseCase.stopRecording(for: observationId)
            recordingState = .completed
        } catch {
            recordingState = .failed
            errorMessage = error.localizedDescription
        }
    }
}
#endif
