#if os(iOS)
import Foundation
import Observation
import SwiftData

// Composition root — wires concrete implementations to use cases
@Observable
public final class AppDependencies {
    public static let shared = AppDependencies()

    // Persistence (set by PECObservationApp after ModelContainer is ready)
    public var observationRepo: ObservationRepositoryPort = InMemoryObservationRepository()
    public var schoolRepo: SchoolRepositoryPort = InMemorySchoolRepository()
    public var teacherRepo: TeacherRepositoryPort = InMemoryTeacherRepository()
    public var syncQueue: SyncQueuePort = InMemorySyncQueue()

    // Network
    public lazy var network: NetworkClientPort = URLSessionNetworkClient(
        baseURL: Bundle.main.infoDictionary?["PEC_API_BASE_URL"] as? String
            ?? "http://localhost:8001"
    )

    // Recording
    public lazy var recorder: AudioRecordingPort = AVFoundationRecorder()

    // Auth token storage (simplified — use Keychain in production)
    public var accessToken: String?

    // Use cases
    public lazy var createObservationUseCase = CreateObservationUseCase(
        repo: observationRepo, syncQueue: syncQueue
    )
    public lazy var recordAudioUseCase = RecordAudioUseCase(
        recorder: recorder, repo: observationRepo, syncQueue: syncQueue
    )
    public lazy var syncUseCase = SyncUseCase(
        syncQueue: syncQueue, network: network, token: { [weak self] in self?.accessToken }
    )

    public func configureWithModelContext(_ context: ModelContext) {
        observationRepo = SwiftDataObservationRepository(context: context)
        syncQueue = SwiftDataSyncQueue(context: context)
    }
}

// In-memory fallbacks (used before SwiftData context is available)
final class InMemoryObservationRepository: ObservationRepositoryPort {
    private var store: [UUID: Observation] = [:]
    func save(_ obs: Observation) { store[obs.id] = obs }
    func fetchAll() -> [Observation] { Array(store.values).sorted { $0.createdAt > $1.createdAt } }
    func fetchById(_ id: UUID) -> Observation? { store[id] }
    func fetchByStatus(_ status: ObservationStatus) -> [Observation] {
        store.values.filter { $0.status == status }
    }
    func delete(_ id: UUID) { store.removeValue(forKey: id) }
}

final class InMemorySchoolRepository: SchoolRepositoryPort {
    private var store: [UUID: School] = [:]
    func save(_ school: School) { store[school.id] = school }
    func fetchAll() -> [School] { Array(store.values) }
    func fetchById(_ id: UUID) -> School? { store[id] }
    func delete(_ id: UUID) { store.removeValue(forKey: id) }
}

final class InMemoryTeacherRepository: TeacherRepositoryPort {
    private var store: [UUID: Teacher] = [:]
    func save(_ teacher: Teacher) { store[teacher.id] = teacher }
    func fetchAll() -> [Teacher] { Array(store.values) }
    func fetchBySchool(_ schoolId: UUID) -> [Teacher] { store.values.filter { $0.schoolId == schoolId } }
    func fetchById(_ id: UUID) -> Teacher? { store[id] }
    func delete(_ id: UUID) { store.removeValue(forKey: id) }
}

final class InMemorySyncQueue: SyncQueuePort {
    private var commands: [UUID: SyncCommand] = [:]
    func enqueue(_ command: SyncCommand) { commands[command.commandId] = command }
    func pendingCommands() -> [SyncCommand] {
        commands.values.filter { $0.status == .pending }.sorted { $0.createdAt < $1.createdAt }
    }
    func markInProgress(_ id: UUID) { commands[id]?.status = .inProgress }
    func markCompleted(_ id: UUID) { commands[id]?.status = .completed }
    func markFailed(_ id: UUID, reason: String) {
        commands[id]?.retryCount += 1
        commands[id]?.failureReason = reason
    }
    func pendingCount() -> Int { commands.values.filter { $0.status == .pending }.count }
}
#endif
