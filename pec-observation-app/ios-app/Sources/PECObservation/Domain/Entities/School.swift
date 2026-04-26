import Foundation

public struct School: Identifiable, Equatable, Codable {
    public let id: UUID
    public var name: String
    public var city: String
    public var district: String
    public var externalReference: String?

    public init(id: UUID = UUID(), name: String, city: String,
                district: String, externalReference: String? = nil) {
        self.id = id
        self.name = name
        self.city = city
        self.district = district
        self.externalReference = externalReference
    }
}
