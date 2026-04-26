package br.gov.educacao.sp.pecobservation.adapters.persistence.entities

import androidx.room.Entity
import androidx.room.PrimaryKey
import br.gov.educacao.sp.pecobservation.domain.entities.SyncCommand
import br.gov.educacao.sp.pecobservation.domain.entities.SyncCommandType
import br.gov.educacao.sp.pecobservation.domain.entities.SyncStatus
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import java.time.Instant
import java.util.UUID

@Entity(tableName = "sync_commands")
data class SyncCommandEntity(
    @PrimaryKey val commandId: String,
    val typeRaw: String,
    val payloadJson: String,
    val statusRaw: String,
    val retryCount: Int,
    val failureReason: String?,
    val createdAt: Long,
) {
    fun toDomain(): SyncCommand {
        val payloadType = object : TypeToken<Map<String, String>>() {}.type
        return SyncCommand(
            commandId     = UUID.fromString(commandId),
            type          = SyncCommandType.valueOf(typeRaw),
            payload       = Gson().fromJson(payloadJson, payloadType),
            status        = SyncStatus.valueOf(statusRaw),
            retryCount    = retryCount,
            failureReason = failureReason,
            createdAt     = Instant.ofEpochMilli(createdAt),
        )
    }

    companion object {
        fun from(cmd: SyncCommand) = SyncCommandEntity(
            commandId     = cmd.commandId.toString(),
            typeRaw       = cmd.type.name,
            payloadJson   = Gson().toJson(cmd.payload),
            statusRaw     = cmd.status.name,
            retryCount    = cmd.retryCount,
            failureReason = cmd.failureReason,
            createdAt     = cmd.createdAt.toEpochMilli(),
        )
    }
}
