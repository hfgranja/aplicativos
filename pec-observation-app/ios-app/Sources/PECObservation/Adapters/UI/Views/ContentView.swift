#if os(iOS)
import SwiftUI

public struct ContentView: View {
    let knowledgeVM:     KnowledgeViewModel
    let bestPracticesVM: BestPracticesViewModel

    public init(knowledgeVM: KnowledgeViewModel, bestPracticesVM: BestPracticesViewModel) {
        self.knowledgeVM     = knowledgeVM
        self.bestPracticesVM = bestPracticesVM
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

            BestPracticesView(vm: bestPracticesVM)
                .tabItem {
                    Label("Boas Práticas", systemImage: "star.circle")
                }

            SyncStatusView()
                .tabItem {
                    Label("Sincronização", systemImage: "arrow.triangle.2.circlepath")
                }
        }
    }
}
#endif
