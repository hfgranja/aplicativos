#if os(iOS)
import SwiftUI

public struct SchoolListView: View {
    @Environment(AppDependencies.self) private var deps
    @State private var schools: [School] = []
    @State private var showingNewSchool = false

    public init() {}

    public var body: some View {
        NavigationStack {
            Group {
                if schools.isEmpty {
                    ContentUnavailableView(
                        "Nenhuma escola",
                        systemImage: "building.2",
                        description: Text("Toque em + para cadastrar a primeira escola")
                    )
                } else {
                    List(schools) { school in
                        VStack(alignment: .leading, spacing: 2) {
                            Text(school.name).font(.headline)
                            Text("\(school.city) · \(school.district)")
                                .font(.subheadline).foregroundStyle(.secondary)
                        }
                        .padding(.vertical, 2)
                    }
                }
            }
            .navigationTitle("Escolas")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button(action: { showingNewSchool = true }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingNewSchool, onDismiss: { loadSchools() }) {
                NewSchoolView()
            }
            .onAppear { loadSchools() }
        }
    }

    private func loadSchools() {
        schools = (try? deps.schoolRepo.fetchAll()) ?? []
    }
}

struct NewSchoolView: View {
    @Environment(AppDependencies.self) private var deps
    @Environment(\.dismiss) private var dismiss
    @State private var name = ""
    @State private var city = ""
    @State private var district = ""
    @State private var externalReference = ""
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            Form {
                Section("Dados da Escola") {
                    TextField("Nome da escola", text: $name)
                    TextField("Município", text: $city)
                    TextField("Diretoria de Ensino", text: $district)
                    TextField("Código INEP (opcional)", text: $externalReference)
                }
                if let error = errorMessage {
                    Section { Text(error).foregroundStyle(.red) }
                }
            }
            .navigationTitle("Nova Escola")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancelar") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Salvar") { save() }
                        .disabled(name.isEmpty || city.isEmpty || district.isEmpty)
                }
            }
        }
    }

    private func save() {
        let school = School(
            name: name, city: city, district: district,
            externalReference: externalReference.isEmpty ? nil : externalReference
        )
        do {
            try deps.schoolRepo.save(school)
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
#endif
