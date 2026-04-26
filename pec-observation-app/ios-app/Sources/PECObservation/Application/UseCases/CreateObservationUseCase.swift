import Foundation

public struct CreateObservationInput {
    public let schoolId: UUID
    public let teacherId: UUID
    public let subject: String
    public let grade: String
    public let lessonTheme: String
    public let lessonObjectives: String

    public init(schoolId: UUID, teacherId: UUID, subject: String, grade: String,
                lessonTheme: String, lessonObjectives: String = "") {
        self.schoolId = schoolId
        self.teacherId = teacherId
        self.subject = subject
        self.grade = grade
        self.lessonTheme = lessonTheme
        self.lessonObjectives = lessonObjectives
    }
}

public final class CreateObservationUseCase {
    private let repo: ObservationRepositoryPort
    private let syncQueue: SyncQueuePort

    public init(repo: ObservationRepositoryPort, syncQueue: SyncQueuePort) {
        self.repo = repo
        self.syncQueue = syncQueue
    }

    public func execute(input: CreateObservationInput) throws -> Observation {
        guard !input.subject.isEmpty, !input.grade.isEmpty, !input.lessonTheme.isEmpty else {
            throw DomainError.validationFailed("Componente, série e tema da aula são obrigatórios")
        }

        let observation = Observation(
            schoolId: input.schoolId,
            teacherId: input.teacherId,
            subject: input.subject,
            grade: input.grade,
            lessonTheme: input.lessonTheme,
            lessonObjectives: input.lessonObjectives,
            status: .draft
        )
        try repo.save(observation)

        let command = SyncCommand(
            type: .createObservation,
            payload: ["observationId": observation.id.uuidString]
        )
        try syncQueue.enqueue(command)

        return observation
    }
}
