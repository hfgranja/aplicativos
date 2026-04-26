import Foundation

public protocol NetworkClientPort {
    func get<T: Decodable>(path: String, token: String?) async throws -> T
    func post<T: Decodable>(path: String, body: Encodable, token: String?) async throws -> T
    func put(url: URL, data: Data, contentType: String) async throws
    func patch<T: Decodable>(path: String, body: Encodable, token: String?) async throws -> T
}
