package br.gov.educacao.sp.pecobservation.domain.entities

import java.time.Instant
import java.util.UUID

enum class SyncCommandType {
    CREATE_OBSERVATION,
    UPDATE_OBSERVATION,
    CREATE_SCHOOL,
    CREATE_TEACHER,
    UPLOAD_AUDIO,
}

enum class SyncStatus {
    PENDING, IN_PROGRESS, COMPLETED, FAILED
}

data class SyncCommand(
    val commandId: UUID = UUID.randomUUID(),
    val type: SyncCommandType,
    val payload: Map<String, String>,
    val status: SyncStatus = SyncStatus.PENDING,
    val retryCount: Int = 0,
    val failureReason: String? = null,
    val createdAt: Instant = Instant.now(),
)
