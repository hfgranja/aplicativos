#if os(iOS)
import SwiftUI

public struct ContentView: View {
    public init() {}

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

            SyncStatusView()
                .tabItem {
                    Label("Sincronização", systemImage: "arrow.triangle.2.circlepath")
                }
        }
    }
}
#endif
