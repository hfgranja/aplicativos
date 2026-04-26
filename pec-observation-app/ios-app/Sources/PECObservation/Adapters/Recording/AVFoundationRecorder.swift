#if os(iOS)
import Foundation
import AVFoundation
import CryptoKit

public final class AVFoundationRecorder: NSObject, AudioRecordingPort {
    private var audioRecorder: AVAudioRecorder?
    private var currentObservationId: UUID?
    private var currentFileURL: URL?
    private var _state: RecordingState = .idle
    private var _elapsedSeconds: Int = 0
    private var timer: Timer?

    public private(set) var currentState: RecordingState {
        get { _state }
        set { _state = newValue }
    }
    public private(set) var elapsedSeconds: Int {
        get { _elapsedSeconds }
        set { _elapsedSeconds = newValue }
    }

    private let recordingSettings: [String: Any] = [
        AVFormatIDKey: kAudioFormatMPEG4AAC,
        AVSampleRateKey: 44100,
        AVNumberOfChannelsKey: 1,
        AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue,
        AVEncoderBitRateKey: 128000,
    ]

    private func recordingsDirectory() -> URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("recordings", isDirectory: true)
    }

    public func requestPermission() async -> Bool {
        await withCheckedContinuation { continuation in
            AVAudioApplication.requestRecordPermission { granted in
                continuation.resume(returning: granted)
            }
        }
    }

    public func startRecording(observationId: UUID) async throws {
        guard _state == .idle || _state == .completed || _state == .failed else {
            throw RecordingError.alreadyRecording
        }
        _state = .preparing
        _elapsedSeconds = 0

        let dir = recordingsDirectory()
        try? FileManager.default.createDirectory(at: dir,
                                                  withIntermediateDirectories: true)
        let fileURL = dir.appendingPathComponent("\(observationId.uuidString).m4a")

        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker])
        try session.setActive(true)

        audioRecorder = try AVAudioRecorder(url: fileURL, settings: recordingSettings)
        audioRecorder?.delegate = self
        audioRecorder?.isMeteringEnabled = true

        guard audioRecorder?.record() == true else {
            _state = .failed
            throw RecordingError.fileCreationFailed
        }

        currentObservationId = observationId
        currentFileURL = fileURL
        _state = .recording
        startTimer()
    }

    public func pauseRecording() async throws {
        guard _state == .recording else { throw RecordingError.notRecording }
        audioRecorder?.pause()
        stopTimer()
        _state = .paused
    }

    public func resumeRecording() async throws {
        guard _state == .paused else { throw RecordingError.notRecording }
        audioRecorder?.record()
        startTimer()
        _state = .recording
    }

    public func stopRecording() async throws -> AudioRecordingResult {
        guard _state == .recording || _state == .paused else {
            throw RecordingError.notRecording
        }
        _state = .stopping
        stopTimer()
        audioRecorder?.stop()

        guard let fileURL = currentFileURL,
              let observationId = currentObservationId else {
            _state = .failed
            throw RecordingError.fileCreationFailed
        }

        try AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)

        let attrs = try FileManager.default.attributesOfItem(atPath: fileURL.path)
        let fileSize = (attrs[.size] as? Int) ?? 0
        let audioData = try Data(contentsOf: fileURL)
        let checksum = SHA256.hash(data: audioData)
            .compactMap { String(format: "%02x", $0) }.joined()

        _state = .completed
        currentObservationId = nil
        currentFileURL = nil

        return AudioRecordingResult(
            observationId: observationId,
            localFileUrl: fileURL,
            durationSeconds: _elapsedSeconds,
            fileSizeBytes: fileSize,
            checksum: checksum,
            codec: "aac"
        )
    }

    private func startTimer() {
        timer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            self?._elapsedSeconds += 1
        }
    }

    private func stopTimer() {
        timer?.invalidate()
        timer = nil
    }
}

extension AVFoundationRecorder: AVAudioRecorderDelegate {
    public func audioRecorderBeginInterruption(_ recorder: AVAudioRecorder) {
        stopTimer()
        _state = .paused
    }

    public func audioRecorderEndInterruption(_ recorder: AVAudioRecorder,
                                              withOptions flags: Int) {
        if flags == AVAudioSession.InterruptionOptions.shouldResume.rawValue {
            try? recorder.record()
            startTimer()
            _state = .recording
        }
    }
}
#endif
