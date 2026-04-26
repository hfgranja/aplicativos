#if os(iOS)
import SwiftUI

public struct ObservationListView: View {
    @Environment(AppDependencies.self) private var deps
    @State private var viewModel: ObservationListViewModel?
    @State private var showingNewObservation = false

    public init() {}

    private func statusColor(_ status: ObservationStatus) -> Color {
        switch status {
        case .draft, .readyToRecord: return .orange
        case .recorded, .audioUploaded: return .blue
        case .transcribing, .transcribed, .generatingFeedback: return .purple
        case .feedbackReady, .inReview: return .yellow
        case .humanReviewed: return .green
        case .approved: return .green
        }
    }

    public var body: some View {
        NavigationStack {
            Group {
                if let vm = viewModel {
                    if vm.observations.isEmpty {
                        ContentUnavailableView(
                            "Nenhuma observação",
                            systemImage: "list.clipboard",
                            description: Text("Toque em + para criar a primeira observação")
                        )
                    } else {
                        List(vm.observations) { obs in
                            NavigationLink(destination: ObservationDetailView(observation: obs)) {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(obs.lessonTheme)
                                        .font(.headline)
                                    Text("\(obs.subject) · \(obs.grade)")
                                        .font(.subheadline)
                                        .foregroundStyle(.secondary)
                                    HStack {
                                        Circle()
                                            .fill(statusColor(obs.status))
                                            .frame(width: 8, height: 8)
                                        Text(obs.status.displayName)
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                    }
                                }
                                .padding(.vertical, 4)
                            }
                        }
                        .refreshable { vm.load() }
                    }
                } else {
                    ProgressView("Carregando...")
                }
            }
            .navigationTitle("Observações")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button(action: { showingNewObservation = true }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingNewObservation, onDismiss: {
                viewModel?.load()
            }) {
                NewObservationView()
            }
            .onAppear {
                if viewModel == nil {
                    viewModel = ObservationListViewModel(repo: deps.observationRepo)
                }
                viewModel?.load()
            }
        }
    }
}

struct ObservationDetailView: View {
    let observation: Observation

    var body: some View {
        List {
            Section("Contexto da Aula") {
                LabeledContent("Componente", value: observation.subject)
                LabeledContent("Série/Ano", value: observation.grade)
                LabeledContent("Tema", value: observation.lessonTheme)
                if !observation.lessonObjectives.isEmpty {
                    VStack(alignment: .leading) {
                        Text("Objetivos").font(.caption).foregroundStyle(.secondary)
                        Text(observation.lessonObjectives)
                    }
                }
            }
            Section("Status") {
                LabeledContent("Situação", value: observation.status.displayName)
                LabeledContent("Criado em",
                               value: observation.createdAt.formatted(date: .abbreviated, time: .shortened))
            }
            if let audio = observation.audioRecording {
                Section("Gravação") {
                    LabeledContent("Duração", value: "\(audio.durationSeconds)s")
                    LabeledContent("Tamanho",
                                   value: ByteCountFormatter.string(fromByteCount: Int64(audio.fileSizeBytes),
                                                                     countStyle: .file))
                }
            }
        }
        .navigationTitle("Observação")
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct NewObservationView: View {
    @Environment(AppDependencies.self) private var deps
    @Environment(\.dismiss) private var dismiss
    @State private var subject = ""
    @State private var grade = ""
    @State private var lessonTheme = ""
    @State private var lessonObjectives = ""
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            Form {
                Section("Dados da Aula") {
                    TextField("Componente curricular", text: $subject)
                    TextField("Série / Ano", text: $grade)
                    TextField("Tema da aula", text: $lessonTheme)
                    TextField("Objetivos da aula", text: $lessonObjectives, axis: .vertical)
                        .lineLimit(3, reservesSpace: true)
                }
                if let error = errorMessage {
                    Section {
                        Text(error).foregroundStyle(.red)
                    }
                }
            }
            .navigationTitle("Nova Observação")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancelar") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Criar") { createObservation() }
                        .disabled(subject.isEmpty || grade.isEmpty || lessonTheme.isEmpty)
                }
            }
        }
    }

    private func createObservation() {
        // Requires school + teacher selection in full implementation
        // For MVP: create with placeholder IDs until school/teacher selection is wired
        let input = CreateObservationInput(
            schoolId: UUID(), teacherId: UUID(),
            subject: subject, grade: grade,
            lessonTheme: lessonTheme, lessonObjectives: lessonObjectives
        )
        do {
            _ = try deps.createObservationUseCase.execute(input: input)
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
#endif
