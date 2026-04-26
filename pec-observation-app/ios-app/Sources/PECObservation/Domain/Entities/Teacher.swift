import Foundation

public struct Teacher: Identifiable, Equatable, Codable {
    public let id: UUID
    public let schoolId: UUID
    public var name: String
    public var registrationNumber: String?
    public var subjects: [String]
    public var grades: [String]

    public init(id: UUID = UUID(), schoolId: UUID, name: String,
                registrationNumber: String? = nil,
                subjects: [String] = [], grades: [String] = []) {
        self.id = id
        self.schoolId = schoolId
        self.name = name
        self.registrationNumber = registrationNumber
        self.subjects = subjects
        self.grades = grades
    }
}
