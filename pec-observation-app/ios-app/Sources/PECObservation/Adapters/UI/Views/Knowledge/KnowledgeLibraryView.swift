import SwiftUI

public struct KnowledgeLibraryView: View {
    @State private var vm: KnowledgeViewModel
    @State private var selectedTab = 0
    @State private var showUploadSheet = false
    @State private var showNewStyleSheet = false

    public init(vm: KnowledgeViewModel) {
        _vm = State(initialValue: vm)
    }

    public var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                Picker("", selection: $selectedTab) {
                    Text("Documentos").tag(0)
                    Text("Estilos").tag(1)
                }
                .pickerStyle(.segmented)
                .padding()

                if selectedTab == 0 {
                    documentsTab
                } else {
                    stylesTab
                }
            }
            .navigationTitle("Base de Conhecimento")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        if selectedTab == 0 { showUploadSheet = true }
                        else { showNewStyleSheet = true }
                    } label: {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showUploadSheet) {
                UploadDocumentSheet { title, type, data, filename in
                    // Upload handled via multipart — placeholder navigates to next step
                    showUploadSheet = false
                }
            }
            .sheet(isPresented: $showNewStyleSheet) {
                NewFeedbackStyleSheet { name, desc, tone, prompt, strengths, improvements, isDefault in
                    Task { await vm.createStyle(name: name, description: desc, tone: tone,
                                               templatePrompt: prompt,
                                               exampleStrengths: strengths,
                                               exampleImprovements: improvements,
                                               isDefault: isDefault) }
                    showNewStyleSheet = false
                }
            }
            .alert("Erro", isPresented: Binding(
                get: { vm.errorMessage != nil },
                set: { if !$0 { vm.errorMessage = nil } }
            )) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(vm.errorMessage ?? "")
            }
        }
        .task { await vm.loadDocuments(); await vm.loadStyles() }
    }

    // MARK: — Documents tab

    private var documentsTab: some View {
        Group {
            if vm.isLoading {
                ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if vm.documents.isEmpty {
                ContentUnavailableView(
                    "Nenhum documento",
                    systemImage: "doc.text.magnifyingglass",
                    description: Text("Adicione documentos da SEDUC para enriquecer o feedback da IA.")
                )
            } else {
                List {
                    ForEach(vm.documents) { doc in
                        DocumentRow(doc: doc)
                    }
                    .onDelete { indices in
                        let ids = indices.map { vm.documents[$0].id }
                        Task { for id in ids { await vm.deleteDocument(id) } }
                    }
                }
            }
        }
    }

    // MARK: — Styles tab

    private var stylesTab: some View {
        Group {
            if vm.styles.isEmpty {
                ContentUnavailableView(
                    "Nenhum estilo",
                    systemImage: "text.badge.star",
                    description: Text("Crie estilos de feedback para personalizar as respostas da IA.")
                )
            } else {
                List {
                    ForEach(vm.styles) { style in
                        StyleRow(style: style)
                    }
                    .onDelete { indices in
                        let ids = indices.map { vm.styles[$0].id }
                        Task { for id in ids { await vm.deleteStyle(id) } }
                    }
                }
            }
        }
    }
}

// MARK: — Sub-views

private struct DocumentRow: View {
    let doc: KnowledgeDocument
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(doc.title).font(.headline)
            HStack {
                Label(doc.documentTypeDisplay, systemImage: "doc.text")
                    .font(.caption).foregroundStyle(.secondary)
                Spacer()
                Text("\(doc.chunkCount) trechos")
                    .font(.caption2).foregroundStyle(.tertiary)
            }
            if let desc = doc.description {
                Text(desc).font(.caption).foregroundStyle(.secondary).lineLimit(2)
            }
        }
        .padding(.vertical, 4)
    }
}

private struct StyleRow: View {
    let style: FeedbackStyle
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(style.name).font(.headline)
                if style.isDefault {
                    Text("Padrão").font(.caption2)
                        .padding(.horizontal, 6).padding(.vertical, 2)
                        .background(Color.accentColor.opacity(0.15))
                        .clipShape(Capsule())
                }
            }
            Text("Tom: \(style.toneDisplay)").font(.caption).foregroundStyle(.secondary)
            Text(style.description).font(.caption).foregroundStyle(.secondary).lineLimit(2)
        }
        .padding(.vertical, 4)
    }
}

// MARK: — Sheets

private struct UploadDocumentSheet: View {
    var onUpload: (String, DocumentType, Data, String) -> Void
    @Environment(\.dismiss) private var dismiss
    @State private var title = ""
    @State private var docType: DocumentType = .seducPolicy
    @State private var showFilePicker = false

    var body: some View {
        NavigationStack {
            Form {
                Section("Informações") {
                    TextField("Título do documento", text: $title)
                    Picker("Tipo", selection: $docType) {
                        ForEach(DocumentType.allCases, id: \.self) { t in
                            Text(t.displayName).tag(t)
                        }
                    }
                }
                Section {
                    Button("Selecionar arquivo (PDF ou TXT)") { showFilePicker = true }
                }
            }
            .navigationTitle("Novo Documento")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancelar") { dismiss() }
                }
            }
        }
    }
}

private struct NewFeedbackStyleSheet: View {
    var onCreate: (String, String, StyleTone, String, [String], [String], Bool) -> Void
    @Environment(\.dismiss) private var dismiss
    @State private var name = ""
    @State private var desc = ""
    @State private var tone: StyleTone = .constructive
    @State private var prompt = ""
    @State private var strengthsText = ""
    @State private var improvementsText = ""
    @State private var isDefault = false

    var body: some View {
        NavigationStack {
            Form {
                Section("Identificação") {
                    TextField("Nome do estilo", text: $name)
                    TextField("Descrição", text: $desc)
                    Picker("Tom", selection: $tone) {
                        ForEach(StyleTone.allCases, id: \.self) { t in
                            Text(t.displayName).tag(t)
                        }
                    }
                    Toggle("Estilo padrão", isOn: $isDefault)
                }
                Section("Instrução para a IA") {
                    TextEditor(text: $prompt)
                        .frame(minHeight: 80)
                }
                Section("Exemplos de pontos fortes (um por linha)") {
                    TextEditor(text: $strengthsText).frame(minHeight: 60)
                }
                Section("Exemplos de pontos de desenvolvimento (um por linha)") {
                    TextEditor(text: $improvementsText).frame(minHeight: 60)
                }
            }
            .navigationTitle("Novo Estilo")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancelar") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Criar") {
                        let strengths = strengthsText.components(separatedBy: "\n").filter { !$0.isEmpty }
                        let improvements = improvementsText.components(separatedBy: "\n").filter { !$0.isEmpty }
                        onCreate(name, desc, tone, prompt, strengths, improvements, isDefault)
                        dismiss()
                    }
                    .disabled(name.isEmpty || prompt.isEmpty)
                }
            }
        }
    }
}
