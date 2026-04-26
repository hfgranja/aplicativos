import Foundation

public protocol ObservationRepositoryPort {
    func save(_ observation: Observation) throws
    func fetchAll() throws -> [Observation]
    func fetchById(_ id: UUID) throws -> Observation?
    func fetchByStatus(_ status: ObservationStatus) throws -> [Observation]
    func delete(_ id: UUID) throws
}
