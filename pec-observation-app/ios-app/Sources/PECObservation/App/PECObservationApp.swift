#if os(iOS)
import SwiftUI
import SwiftData

@main
public struct PECObservationApp: App {
    private let container: ModelContainer

    public init() {
        let schema = Schema([
            ObservationEntity.self,
            SyncCommandEntity.self,
            SchoolEntity.self,
            TeacherEntity.self,
        ])
        let config = ModelConfiguration(
            schema: schema,
            isStoredInMemoryOnly: false,
            cloudKitDatabase: .none  // Explicit: no iCloud backup for audio paths
        )
        do {
            container = try ModelContainer(for: schema, configurations: [config])
        } catch {
            fatalError("Failed to create ModelContainer: \(error)")
        }
    }

    public var body: some Scene {
        WindowGroup {
            ContentView()
                .modelContainer(container)
                .environment(AppDependencies.shared)
                .onAppear {
                    AppDependencies.shared.configureWithModelContext(container.mainContext)
                }
        }
    }
}
#endif
