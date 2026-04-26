#if os(iOS)
import Foundation

public final class URLSessionNetworkClient: NetworkClientPort {
    private let baseURL: String
    private let session: URLSession

    private let decoder: JSONDecoder = {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        d.dateDecodingStrategy = .iso8601
        return d
    }()

    private let encoder: JSONEncoder = {
        let e = JSONEncoder()
        e.keyEncodingStrategy = .convertToSnakeCase
        return e
    }()

    public init(baseURL: String, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
    }

    public func get<T: Decodable>(path: String, token: String?) async throws -> T {
        let request = try buildRequest(method: "GET", path: path, body: nil as Data?, token: token)
        return try await perform(request)
    }

    public func post<T: Decodable>(path: String, body: Encodable, token: String?) async throws -> T {
        let bodyData = try encoder.encode(body)
        var request = try buildRequest(method: "POST", path: path, body: bodyData, token: token)
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        return try await perform(request)
    }

    public func put(url: URL, data: Data, contentType: String) async throws {
        var request = URLRequest(url: url)
        request.httpMethod = "PUT"
        request.setValue(contentType, forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 300
        let (_, response) = try await session.upload(for: request, from: data)
        guard let http = response as? HTTPURLResponse,
              (200...299).contains(http.statusCode) else {
            let code = (response as? HTTPURLResponse)?.statusCode ?? 0
            throw NetworkError.serverError(code)
        }
    }

    public func patch<T: Decodable>(path: String, body: Encodable, token: String?) async throws -> T {
        let bodyData = try encoder.encode(body)
        var request = try buildRequest(method: "PATCH", path: path, body: bodyData, token: token)
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        return try await perform(request)
    }

    private func buildRequest(method: String, path: String, body: Data?, token: String?) throws -> URLRequest {
        guard let url = URL(string: baseURL + path) else {
            throw NetworkError.decodingFailed("Invalid URL: \(baseURL + path)")
        }
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.timeoutInterval = 30
        request.httpBody = body
        if let token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        return request
    }

    private func perform<T: Decodable>(_ request: URLRequest) async throws -> T {
        do {
            let (data, response) = try await session.data(for: request)
            guard let http = response as? HTTPURLResponse else {
                throw NetworkError.serverError(0)
            }
            switch http.statusCode {
            case 200...299:
                do {
                    return try decoder.decode(T.self, from: data)
                } catch {
                    throw NetworkError.decodingFailed(error.localizedDescription)
                }
            case 401:
                throw NetworkError.unauthorized
            default:
                throw NetworkError.serverError(http.statusCode)
            }
        } catch let error as NetworkError {
            throw error
        } catch {
            if (error as NSError).code == NSURLErrorNotConnectedToInternet {
                throw NetworkError.noConnection
            }
            throw NetworkError.serverError(0)
        }
    }
}
#endif
