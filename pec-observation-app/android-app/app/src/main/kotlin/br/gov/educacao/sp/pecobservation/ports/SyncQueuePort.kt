package br.gov.educacao.sp.pecobservation.ports

import br.gov.educacao.sp.pecobservation.domain.entities.SyncCommand
import java.util.UUID

interface SyncQueuePort {
    suspend fun enqueue(command: SyncCommand)
    suspend fun pendingCommands(): List<SyncCommand>
    suspend fun markInProgress(commandId: UUID)
    suspend fun markCompleted(commandId: UUID)
    suspend fun markFailed(commandId: UUID, reason: String)
    suspend fun pendingCount(): Int
}
