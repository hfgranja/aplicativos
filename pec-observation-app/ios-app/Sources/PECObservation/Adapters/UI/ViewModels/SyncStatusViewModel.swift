#if os(iOS)
import Foundation
import Observation

@Observable
public final class SyncStatusViewModel {
    private let syncQueue: SyncQueuePort
    private let syncUseCase: SyncUseCase
    public var pendingCount: Int = 0
    public var lastSyncAt: Date?
    public var syncError: String?
    public var isSyncing = false

    public init(syncQueue: SyncQueuePort, syncUseCase: SyncUseCase) {
        self.syncQueue = syncQueue
        self.syncUseCase = syncUseCase
    }

    public func refreshStatus() {
        pendingCount = (try? syncQueue.pendingCount()) ?? 0
    }

    public func syncNow() async {
        guard !isSyncing else { return }
        isSyncing = true
        syncError = nil
        await syncUseCase.processPendingCommands()
        pendingCount = (try? syncQueue.pendingCount()) ?? 0
        lastSyncAt = Date()
        isSyncing = false
    }
}
#endif
