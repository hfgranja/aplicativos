#if os(iOS)
import SwiftUI

public struct RecordingView: View {
    let observationId: UUID
    @Environment(AppDependencies.self) private var deps
    @State private var viewModel: RecordingViewModel?

    public init(observationId: UUID) {
        self.observationId = observationId
    }

    public var body: some View {
        VStack(spacing: 32) {
            if let vm = viewModel {
                // State display
                VStack(spacing: 8) {
                    stateIcon(vm.recordingState)
                        .font(.system(size: 64))
                    Text(stateLabel(vm.recordingState))
                        .font(.title2)
                        .foregroundStyle(.secondary)
                }

                // Timer
                Text(vm.formattedTime)
                    .font(.system(size: 56, weight: .thin, design: .monospaced))
                    .foregroundStyle(vm.recordingState == .recording ? .red : .primary)

                // Error
                if let error = vm.errorMessage {
                    Text(error)
                        .foregroundStyle(.red)
                        .font(.caption)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                }

                // Controls
                HStack(spacing: 40) {
                    switch vm.recordingState {
                    case .idle, .completed, .failed:
                        Button(action: { Task { await vm.startRecording(observationId: observationId) } }) {
                            Circle()
                                .fill(.red)
                                .frame(width: 72, height: 72)
                                .overlay { Image(systemName: "mic").foregroundStyle(.white).font(.title) }
                        }

                    case .recording:
                        Button(action: { Task { await vm.pauseRecording() } }) {
                            Circle().stroke(.orange, lineWidth: 3).frame(width: 56, height: 56)
                                .overlay { Image(systemName: "pause").foregroundStyle(.orange).font(.title2) }
                        }
                        Button(action: { Task { await vm.stopRecording(observationId: observationId) } }) {
                            Circle().stroke(.red, lineWidth: 3).frame(width: 72, height: 72)
                                .overlay { Image(systemName: "stop.fill").foregroundStyle(.red).font(.title) }
                        }

                    case .paused:
                        Button(action: { Task { await vm.resumeRecording() } }) {
                            Circle().stroke(.green, lineWidth: 3).frame(width: 56, height: 56)
                                .overlay { Image(systemName: "play").foregroundStyle(.green).font(.title2) }
                        }
                        Button(action: { Task { await vm.stopRecording(observationId: observationId) } }) {
                            Circle().stroke(.red, lineWidth: 3).frame(width: 72, height: 72)
                                .overlay { Image(systemName: "stop.fill").foregroundStyle(.red).font(.title) }
                        }

                    case .preparing, .stopping:
                        ProgressView()
                    }
                }

                if vm.recordingState == .completed, let result = vm.lastResult {
                    VStack(spacing: 4) {
                        Image(systemName: "checkmark.circle.fill").foregroundStyle(.green).font(.largeTitle)
                        Text("Gravação salva").font(.headline)
                        Text("Aguardando conexão para envio")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                }
            } else {
                ProgressView()
            }
        }
        .padding()
        .navigationTitle("Gravação")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            if viewModel == nil {
                viewModel = RecordingViewModel(recordAudioUseCase: deps.recordAudioUseCase)
            }
        }
    }

    private func stateIcon(_ state: RecordingState) -> Image {
        switch state {
        case .idle: return Image(systemName: "mic.slash")
        case .preparing: return Image(systemName: "mic")
        case .recording: return Image(systemName: "waveform")
        case .paused: return Image(systemName: "pause.circle")
        case .stopping: return Image(systemName: "stop.circle")
        case .completed: return Image(systemName: "checkmark.circle")
        case .failed: return Image(systemName: "exclamationmark.circle")
        }
    }

    private func stateLabel(_ state: RecordingState) -> String {
        switch state {
        case .idle: return "Pronto para gravar"
        case .preparing: return "Preparando..."
        case .recording: return "Gravando"
        case .paused: return "Pausado"
        case .stopping: return "Finalizando..."
        case .completed: return "Concluído"
        case .failed: return "Erro"
        }
    }
}
#endif
