#if os(iOS)
import SwiftUI

public struct ContentView: View {
    let knowledgeVM: KnowledgeViewModel

    public init(knowledgeVM: KnowledgeViewModel) {
        self.knowledgeVM = knowledgeVM
    }

    public var body: some View {
        TabView {
            ObservationListView()
                .tabItem {
                    Label("Observações", systemImage: "list.clipboard")
                }

            SchoolListView()
                .tabItem {
                    Label("Escolas", systemImage: "building.2")
                }

            KnowledgeLibraryView(vm: knowledgeVM)
                .tabItem {
                    Label("Biblioteca", systemImage: "books.vertical")
                }

            SyncStatusView()
                .tabItem {
                    Label("Sincronização", systemImage: "arrow.triangle.2.circlepath")
                }
        }
    }
}
#endif
