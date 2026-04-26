import XCTest
@testable import PECObservation

final class CreateObservationUseCaseTests: XCTestCase {

    func testCreatesObservationInDraftStatus() throws {
        let repo = MockObservationRepository()
        let queue = MockSyncQueue()
        let useCase = CreateObservationUseCase(repo: repo, syncQueue: queue)

        let result = try useCase.execute(input: CreateObservationInput(
            schoolId: UUID(), teacherId: UUID(),
            subject: "Matemática", grade: "7º ano",
            lessonTheme: "Frações", lessonObjectives: "Identificar frações"
        ))

        XCTAssertEqual(result.status, .draft)
        XCTAssertEqual(repo.saved.count, 1)
        XCTAssertEqual(queue.enqueued.count, 1)
        XCTAssertEqual(queue.enqueued[0].type, .createObservation)
    }

    func testThrowsWhenSubjectEmpty() {
        let repo = MockObservationRepository()
        let queue = MockSyncQueue()
        let useCase = CreateObservationUseCase(repo: repo, syncQueue: queue)

        XCTAssertThrowsError(try useCase.execute(input: CreateObservationInput(
            schoolId: UUID(), teacherId: UUID(),
            subject: "", grade: "7º ano", lessonTheme: "Frações"
        )))
    }

    func testThrowsWhenGradeEmpty() {
        let repo = MockObservationRepository()
        let queue = MockSyncQueue()
        let useCase = CreateObservationUseCase(repo: repo, syncQueue: queue)

        XCTAssertThrowsError(try useCase.execute(input: CreateObservationInput(
            schoolId: UUID(), teacherId: UUID(),
            subject: "Matemática", grade: "", lessonTheme: "Frações"
        )))
    }

    func testIsReadyForRecordingWhenFieldsFilled() {
        let obs = Observation(schoolId: UUID(), teacherId: UUID(),
                              subject: "Matemática", grade: "5º ano",
                              lessonTheme: "Frações")
        XCTAssertTrue(obs.isReadyForRecording)
    }

    func testIsNotReadyForRecordingWhenSubjectEmpty() {
        let obs = Observation(schoolId: UUID(), teacherId: UUID(),
                              subject: "", grade: "5º ano",
                              lessonTheme: "Frações")
        XCTAssertFalse(obs.isReadyForRecording)
    }
}

// MARK: — Mocks

final class MockObservationRepository: ObservationRepositoryPort {
    var saved: [Observation] = []
    var store: [UUID: Observation] = [:]

    func save(_ observation: Observation) throws {
        saved.append(observation)
        store[observation.id] = observation
    }
    func fetchAll() throws -> [Observation] { Array(store.values) }
    func fetchById(_ id: UUID) throws -> Observation? { store[id] }
    func fetchByStatus(_ status: ObservationStatus) throws -> [Observation] {
        store.values.filter { $0.status == status }
    }
    func delete(_ id: UUID) throws { store.removeValue(forKey: id) }
}

final class MockSyncQueue: SyncQueuePort {
    var enqueued: [SyncCommand] = []
    var store: [UUID: SyncCommand] = [:]

    func enqueue(_ command: SyncCommand) throws {
        enqueued.append(command)
        store[command.commandId] = command
    }
    func pendingCommands() throws -> [SyncCommand] {
        store.values.filter { $0.status == .pending }
    }
    func markInProgress(_ commandId: UUID) throws { store[commandId]?.status = .inProgress }
    func markCompleted(_ commandId: UUID) throws { store[commandId]?.status = .completed }
    func markFailed(_ commandId: UUID, reason: String) throws {
        store[commandId]?.retryCount += 1
        store[commandId]?.failureReason = reason
    }
    func pendingCount() throws -> Int { store.values.filter { $0.status == .pending }.count }
}
