import Foundation

@Observable
public final class KnowledgeViewModel {
    public var documents: [KnowledgeDocument] = []
    public var styles: [FeedbackStyle] = []
    public var isLoading = false
    public var errorMessage: String?
    public var uploadProgress: Double = 0

    private let network: NetworkClientPort
    private let accessToken: String

    public init(network: NetworkClientPort, accessToken: String) {
        self.network = network
        self.accessToken = accessToken
    }

    // MARK: — Documents

    public func loadDocuments() async {
        isLoading = true
        defer { isLoading = false }
        do {
            let response: [KnowledgeDocument] = try await network.get(
                path: "/api/v1/knowledge/documents", token: accessToken
            )
            documents = response
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    public func deleteDocument(_ id: String) async {
        do {
            _ = try await network.delete(path: "/api/v1/knowledge/documents/\(id)", token: accessToken)
            documents.removeAll { $0.id == id }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    // MARK: — Feedback Styles

    public func loadStyles() async {
        do {
            let response: [FeedbackStyle] = try await network.get(
                path: "/api/v1/knowledge/feedback-styles", token: accessToken
            )
            styles = response
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    public func createStyle(name: String, description: String, tone: StyleTone,
                            templatePrompt: String, exampleStrengths: [String],
                            exampleImprovements: [String], isDefault: Bool) async {
        isLoading = true
        defer { isLoading = false }
        do {
            let body: [String: Any] = [
                "name": name, "description": description,
                "tone": tone.rawValue, "template_prompt": templatePrompt,
                "example_strengths": exampleStrengths,
                "example_improvements": exampleImprovements,
                "is_default": isDefault,
            ]
            let created: FeedbackStyle = try await network.post(
                path: "/api/v1/knowledge/feedback-styles", body: body, token: accessToken
            )
            styles.append(created)
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    public func deleteStyle(_ id: String) async {
        do {
            _ = try await network.delete(path: "/api/v1/knowledge/feedback-styles/\(id)", token: accessToken)
            styles.removeAll { $0.id == id }
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
