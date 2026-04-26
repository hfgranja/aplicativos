import Foundation

public protocol SyncQueuePort {
    func enqueue(_ command: SyncCommand) throws
    func pendingCommands() throws -> [SyncCommand]
    func markInProgress(_ commandId: UUID) throws
    func markCompleted(_ commandId: UUID) throws
    func markFailed(_ commandId: UUID, reason: String) throws
    func pendingCount() throws -> Int
}
