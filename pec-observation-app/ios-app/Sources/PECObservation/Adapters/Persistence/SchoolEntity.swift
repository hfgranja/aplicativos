#if os(iOS)
import Foundation
import SwiftData

@Model
public final class SchoolEntity {
    @Attribute(.unique) public var id: UUID
    public var name: String
    public var city: String
    public var district: String
    public var externalReference: String?
    public var createdAt: Date

    public init(id: UUID = UUID(), name: String, city: String, district: String,
                externalReference: String? = nil, createdAt: Date = Date()) {
        self.id = id
        self.name = name
        self.city = city
        self.district = district
        self.externalReference = externalReference
        self.createdAt = createdAt
    }

    public func toDomain() -> School {
        School(id: id, name: name, city: city, district: district,
               externalReference: externalReference)
    }
}

@Model
public final class TeacherEntity {
    @Attribute(.unique) public var id: UUID
    public var schoolId: UUID
    public var name: String
    public var registrationNumber: String?
    public var subjectsJSON: String  // JSON-encoded [String]
    public var gradesJSON: String    // JSON-encoded [String]
    public var createdAt: Date

    public init(id: UUID = UUID(), schoolId: UUID, name: String,
                registrationNumber: String? = nil,
                subjects: [String] = [], grades: [String] = [],
                createdAt: Date = Date()) {
        self.id = id
        self.schoolId = schoolId
        self.name = name
        self.registrationNumber = registrationNumber
        self.subjectsJSON = (try? String(data: JSONEncoder().encode(subjects), encoding: .utf8)) ?? "[]"
        self.gradesJSON = (try? String(data: JSONEncoder().encode(grades), encoding: .utf8)) ?? "[]"
        self.createdAt = createdAt
    }

    public func toDomain() -> Teacher {
        let subjects = (try? JSONDecoder().decode([String].self,
                        from: Data(subjectsJSON.utf8))) ?? []
        let grades = (try? JSONDecoder().decode([String].self,
                      from: Data(gradesJSON.utf8))) ?? []
        return Teacher(id: id, schoolId: schoolId, name: name,
                       registrationNumber: registrationNumber,
                       subjects: subjects, grades: grades)
    }
}
#endif
