import Foundation

public protocol SchoolRepositoryPort {
    func save(_ school: School) throws
    func fetchAll() throws -> [School]
    func fetchById(_ id: UUID) throws -> School?
    func delete(_ id: UUID) throws
}

public protocol TeacherRepositoryPort {
    func save(_ teacher: Teacher) throws
    func fetchAll() throws -> [Teacher]
    func fetchBySchool(_ schoolId: UUID) throws -> [Teacher]
    func fetchById(_ id: UUID) throws -> Teacher?
    func delete(_ id: UUID) throws
}
