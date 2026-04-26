#if os(iOS)
import Foundation
import Observation

@Observable
public final class ObservationListViewModel {
    private let repo: ObservationRepositoryPort
    public var observations: [Observation] = []
    public var isLoading = false
    public var errorMessage: String?

    public init(repo: ObservationRepositoryPort) {
        self.repo = repo
    }

    public func load() {
        isLoading = true
        errorMessage = nil
        do {
            observations = try repo.fetchAll()
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    public func delete(_ observation: Observation) {
        try? repo.delete(observation.id)
        load()
    }
}
#endif
