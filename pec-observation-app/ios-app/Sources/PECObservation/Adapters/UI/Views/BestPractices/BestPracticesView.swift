import SwiftUI
#if os(iOS)
import AVKit
#endif

public struct BestPracticesView: View {
    @State var vm: BestPracticesViewModel

    private let tabs = ["Biblioteca", "Em análise"]

    public init(vm: BestPracticesViewModel) { _vm = State(initialValue: vm) }

    public var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Segmented control
                Picker("", selection: $vm.selectedStatus) {
                    Text("Publicados").tag("published")
                    Text("Rascunhos").tag("draft")
                }
                .pickerStyle(.segmented)
                .padding(.horizontal).padding(.top, 8)

                if vm.isLoading {
                    ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if vm.cards.isEmpty {
                    emptyState
                } else {
                    cardList
                }
            }
            .navigationTitle("Boas Práticas")
            .navigationBarTitleDisplayMode(.large)
            .task(id: vm.selectedStatus) { await vm.loadLibrary() }
            .alert("Erro", isPresented: Binding(
                get: { vm.errorMessage != nil },
                set: { if !$0 { vm.errorMessage = nil } }
            )) {
                Button("OK") { vm.errorMessage = nil }
            } message: {
                Text(vm.errorMessage ?? "")
            }
        }
    }

    private var cardList: some View {
        ScrollView {
            LazyVStack(spacing: 12) {
                infoHeader
                ForEach(vm.cards) { card in
                    NavigationLink {
                        PracticeDetailView(card: card, vm: vm)
                    } label: {
                        PracticeCardRow(card: card)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding()
        }
    }

    private var infoHeader: some View {
        HStack {
            Image(systemName: "sparkles")
                .foregroundStyle(.yellow)
            Text("Momentos exemplares extraídos automaticamente das observações e anonimizados para proteger a identidade dos professores.")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(12)
        .background(.blue.opacity(0.06), in: RoundedRectangle(cornerRadius: 10))
    }

    private var emptyState: some View {
        VStack(spacing: 12) {
            Text("⭐️").font(.system(size: 48))
            Text("Nenhuma boa prática ainda")
                .font(.headline)
            Text("As boas práticas são extraídas automaticamente quando uma observação é aprovada.")
                .multilineTextAlignment(.center)
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .padding(40)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// MARK: - Card Row

struct PracticeCardRow: View {
    let card: BestPracticeCard

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(card.criterionEnum?.emoji ?? "📚")
                Text(card.criterionEnum?.displayName ?? card.criterion)
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.secondary)
                Spacer()
                if card.hasAudio {
                    Label("Áudio", systemImage: "waveform")
                        .font(.caption2)
                        .foregroundStyle(.blue)
                }
                if card.hasVideo {
                    Label("Vídeo", systemImage: "play.rectangle.fill")
                        .font(.caption2)
                        .foregroundStyle(.purple)
                } else if card.videoStatus == "processing" {
                    Label("Gerando…", systemImage: "film.stack")
                        .font(.caption2)
                        .foregroundStyle(.orange)
                }
            }
            Text(card.title)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(.primary)
            Text(card.excerpt)
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(2)
            HStack(spacing: 6) {
                Tag(card.subject)
                Tag(card.grade)
            }
        }
        .padding()
        .background(.background, in: RoundedRectangle(cornerRadius: 14))
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(.separator, lineWidth: 0.5))
    }
}

struct Tag: View {
    let text: String
    init(_ text: String) { self.text = text }
    var body: some View {
        Text(text)
            .font(.caption2.weight(.medium))
            .padding(.horizontal, 8).padding(.vertical, 3)
            .background(.blue.opacity(0.1), in: Capsule())
            .foregroundStyle(.blue)
    }
}

// MARK: - Detail View

struct PracticeDetailView: View {
    let card: BestPracticeCard
    @State var vm: BestPracticesViewModel
    @State private var showDistributeSheet = false
    @State private var publishTitle = ""
    @State private var videoURL: URL? = nil
    @State private var videoLoading = false
    @State private var showVideoPlayer = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // Criterion badge
                Label(card.criterionEnum?.displayName ?? card.criterion,
                      systemImage: "checkmark.seal")
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(.blue)

                // Subject + grade
                HStack {
                    Tag(card.subject)
                    Tag(card.grade)
                }

                Divider()

                // Excerpt
                VStack(alignment: .leading, spacing: 4) {
                    Label("Trecho da aula (anonimizado)", systemImage: "text.quote")
                        .font(.caption.weight(.semibold)).foregroundStyle(.secondary)
                    Text(card.excerpt)
                        .font(.body)
                        .padding(12)
                        .background(.gray.opacity(0.08), in: RoundedRectangle(cornerRadius: 10))
                }

                // AI explanation
                VStack(alignment: .leading, spacing: 4) {
                    Label("Por que é uma boa prática?", systemImage: "brain")
                        .font(.caption.weight(.semibold)).foregroundStyle(.secondary)
                    Text(card.aiExplanation).font(.subheadline)
                }

                // Rubric
                if !card.rubricAlignment.isEmpty {
                    VStack(alignment: .leading, spacing: 6) {
                        Label("Alinhamento SEDUC", systemImage: "list.bullet.clipboard")
                            .font(.caption.weight(.semibold)).foregroundStyle(.secondary)
                        ForEach(card.rubricAlignment, id: \.self) { item in
                            Label(item, systemImage: "checkmark.circle.fill")
                                .font(.caption)
                                .foregroundStyle(.green)
                        }
                    }
                }

                // Video section
                #if os(iOS)
                videoSection
                #endif

                Divider()

                // Actions
                if card.status == "draft" {
                    VStack(spacing: 10) {
                        TextField("Título (pode editar antes de publicar)", text: $publishTitle)
                            .textFieldStyle(.roundedBorder)
                        Button {
                            Task { await vm.publish(cardId: card.id,
                                                    title: publishTitle.isEmpty ? card.title : publishTitle) }
                        } label: {
                            Label("Publicar na biblioteca", systemImage: "checkmark.circle")
                                .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.borderedProminent)
                    }
                } else if card.status == "published" {
                    Button {
                        showDistributeSheet = true
                    } label: {
                        Label("Enviar para professores", systemImage: "paperplane.fill")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                }
            }
            .padding()
        }
        .navigationTitle(card.title)
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showDistributeSheet) {
            DistributeSheet(card: card, vm: vm)
        }
        #if os(iOS)
        .fullScreenCover(isPresented: $showVideoPlayer) {
            if let url = videoURL {
                VideoPlayerView(url: url, onClose: { showVideoPlayer = false })
            }
        }
        #endif
        .onAppear { publishTitle = card.title }
    }

    #if os(iOS)
    @ViewBuilder
    private var videoSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("Vídeo da boa prática", systemImage: "play.rectangle.fill")
                .font(.caption.weight(.semibold)).foregroundStyle(.secondary)

            switch card.videoStatus {
            case "ready":
                Button {
                    guard !videoLoading else { return }
                    videoLoading = true
                    Task {
                        videoURL = await vm.fetchVideoUrl(cardId: card.id)
                        videoLoading = false
                        if videoURL != nil { showVideoPlayer = true }
                    }
                } label: {
                    if videoLoading {
                        ProgressView()
                            .frame(maxWidth: .infinity)
                    } else {
                        Label("Assistir vídeo anime", systemImage: "play.fill")
                            .frame(maxWidth: .infinity)
                    }
                }
                .buttonStyle(.borderedProminent)
                .tint(.purple)
                .disabled(videoLoading)

                if let dur = card.videoDurationS {
                    Text("Duração: \(dur / 60)m \(dur % 60)s")
                        .font(.caption2).foregroundStyle(.secondary)
                }

            case "processing":
                HStack {
                    ProgressView().scaleEffect(0.8)
                    Text("Gerando vídeo… aguarde")
                        .font(.caption).foregroundStyle(.secondary)
                }
                .padding(10)
                .background(.orange.opacity(0.08), in: RoundedRectangle(cornerRadius: 8))

            case "failed":
                Label("Falha na geração do vídeo", systemImage: "exclamationmark.triangle")
                    .font(.caption).foregroundStyle(.red)

            default: // pending
                Label("Vídeo será gerado em breve", systemImage: "clock")
                    .font(.caption).foregroundStyle(.secondary)
            }
        }
    }
    #endif
}

// MARK: - Video Player (iOS only)

#if os(iOS)
private struct VideoPlayerView: View {
    let url: URL
    let onClose: () -> Void

    var body: some View {
        ZStack(alignment: .topTrailing) {
            VideoPlayer(player: AVPlayer(url: url))
                .ignoresSafeArea()
            Button(action: onClose) {
                Image(systemName: "xmark.circle.fill")
                    .font(.title)
                    .foregroundStyle(.white)
                    .shadow(radius: 4)
            }
            .padding()
        }
    }
}
#endif

// MARK: - Distribute Sheet

struct DistributeSheet: View {
    let card: BestPracticeCard
    @State var vm: BestPracticesViewModel
    @State private var teacherIds = ""
    @State private var message    = ""
    @State private var sending    = false
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Section("Destinatários") {
                    TextField("IDs dos professores (vírgula para múltiplos)", text: $teacherIds, axis: .vertical)
                }
                Section("Mensagem opcional") {
                    TextField("Ex: Esta aula exemplifica bem o uso de avaliação formativa…", text: $message, axis: .vertical)
                        .lineLimit(4...)
                }
                Section {
                    Text("⚠️ O conteúdo enviado é completamente anonimizado — nenhuma informação sobre o professor original é compartilhada.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Enviar para Professores")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancelar") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Enviar") {
                        let ids = teacherIds.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) }
                        guard !ids.isEmpty else { return }
                        sending = true
                        Task {
                            await vm.distribute(cardId: card.id, teacherIds: ids, message: message)
                            sending = false
                            dismiss()
                        }
                    }
                    .disabled(teacherIds.isEmpty || sending)
                }
            }
        }
    }
}
