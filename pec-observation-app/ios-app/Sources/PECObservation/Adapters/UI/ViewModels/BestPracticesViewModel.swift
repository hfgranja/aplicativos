import Foundation

@Observable
public final class BestPracticesViewModel {
    public var cards:         [BestPracticeCard] = []
    public var distributions: [Distribution]     = []
    public var isLoading:     Bool                = false
    public var errorMessage:  String?             = nil
    public var selectedStatus: String             = "published"

    private let network: any NetworkClientPort

    public init(network: any NetworkClientPort) {
        self.network = network
    }

    // MARK: - PEC actions

    public func loadLibrary(status: String? = nil) async {
        isLoading = true
        defer { isLoading = false }
        do {
            let s = status ?? selectedStatus
            let path = s.isEmpty
                ? "/api/v1/best-practices"
                : "/api/v1/best-practices?status=\(s)"
            let response: [String: Any] = try await network.get(path)
            let items = response["items"] as? [[String: Any]] ?? []
            cards = items.compactMap { parseCard($0) }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    public func publish(cardId: String, title: String) async {
        do {
            let _: [String: Any] = try await network.post(
                "/api/v1/best-practices/\(cardId)/publish",
                body: ["title": title]
            )
            await loadLibrary()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    public func distribute(cardId: String, teacherIds: [String], message: String) async {
        do {
            let _: [String: Any] = try await network.post(
                "/api/v1/best-practices/\(cardId)/distribute",
                body: ["teacher_ids": teacherIds, "message": message]
            )
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    public func archive(cardId: String) async {
        do {
            try await network.delete("/api/v1/best-practices/\(cardId)")
            cards.removeAll { $0.id == cardId }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - Teacher actions

    public func loadMyDistributions(teacherId: String) async {
        isLoading = true
        defer { isLoading = false }
        do {
            let response: [String: Any] = try await network.get(
                "/api/v1/best-practices/distributions/my?teacher_id=\(teacherId)"
            )
            let items = response["items"] as? [[String: Any]] ?? []
            distributions = items.compactMap { parseDist($0) }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - Parsing helpers

    public func fetchVideoUrl(cardId: String) async -> URL? {
        do {
            let response: [String: Any] = try await network.get(
                "/api/v1/best-practices/\(cardId)/video-url"
            )
            if let urlString = response["url"] as? String {
                return URL(string: urlString)
            }
        } catch {
            errorMessage = error.localizedDescription
        }
        return nil
    }

    private func parseCard(_ m: [String: Any]) -> BestPracticeCard? {
        guard let id    = m["id"]    as? String,
              let title = m["title"] as? String else { return nil }
        return BestPracticeCard(
            id:             id,
            title:          title,
            criterion:      m["criterion"]   as? String ?? "",
            subject:        m["subject"]     as? String ?? "",
            grade:          m["grade"]       as? String ?? "",
            excerpt:        m["excerpt"]     as? String ?? "",
            aiExplanation:  m["ai_explanation"] as? String ?? "",
            rubricAlignment: m["rubric_alignment"] as? [String] ?? [],
            tags:           m["tags"]        as? [String] ?? [],
            status:         m["status"]      as? String ?? "",
            hasAudio:       m["has_audio"]   as? Bool ?? false,
            audioUrl:       m["audio_url"]   as? String,
            hasVideo:       m["has_video"]   as? Bool ?? false,
            videoStatus:    m["video_status"] as? String ?? "pending",
            videoDurationS: m["video_duration_s"] as? Int,
            createdAt:      m["created_at"]  as? String ?? "",
            publishedAt:    m["published_at"] as? String
        )
    }

    private func parseDist(_ m: [String: Any]) -> Distribution? {
        guard let id   = m["distribution_id"] as? String,
              let card = m["card"] as? [String: Any],
              let c    = parseCard(card) else { return nil }
        return Distribution(
            id:       id,
            card:     c,
            message:  m["message"]   as? String ?? "",
            sentAt:   m["sent_at"]   as? String ?? "",
            viewedAt: m["viewed_at"] as? String
        )
    }
}
