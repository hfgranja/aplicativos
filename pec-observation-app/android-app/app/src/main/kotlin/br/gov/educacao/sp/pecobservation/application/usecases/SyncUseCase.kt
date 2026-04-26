package br.gov.educacao.sp.pecobservation.application.usecases

import android.util.Log
import br.gov.educacao.sp.pecobservation.domain.entities.SyncCommandType
import br.gov.educacao.sp.pecobservation.ports.NetworkClientPort
import br.gov.educacao.sp.pecobservation.ports.SyncQueuePort
import kotlinx.coroutines.delay
import java.util.UUID
import javax.inject.Inject

private const val TAG = "SyncUseCase"
private const val MAX_RETRIES = 5

class SyncUseCase @Inject constructor(
    private val syncQueue: SyncQueuePort,
    private val network: NetworkClientPort,
) {
    suspend fun execute(): SyncResult {
        val pending = syncQueue.pendingCommands().sortedBy { it.createdAt }
        var succeeded = 0
        var failed = 0

        for (command in pending) {
            syncQueue.markInProgress(command.commandId)
            try {
                when (command.type) {
                    SyncCommandType.CREATE_OBSERVATION -> {
                        val obsId = command.payload["observationId"]!!
                        network.post("/api/v1/observations", mapOf("id" to obsId))
                    }
                    SyncCommandType.UPDATE_OBSERVATION -> {
                        val obsId = command.payload["observationId"]!!
                        network.patch("/api/v1/observations/$obsId", command.payload)
                    }
                    SyncCommandType.CREATE_SCHOOL -> {
                        network.post("/api/v1/schools", command.payload)
                    }
                    SyncCommandType.CREATE_TEACHER -> {
                        network.post("/api/v1/teachers", command.payload)
                    }
                    SyncCommandType.UPLOAD_AUDIO -> processAudioUpload(command.payload)
                }
                syncQueue.markCompleted(command.commandId)
                succeeded++
            } catch (e: Exception) {
                Log.w(TAG, "Command ${command.commandId} failed: ${e.message}")
                val retries = command.retryCount
                if (retries < MAX_RETRIES) {
                    delay(exponentialBackoffMs(retries))
                    syncQueue.markFailed(command.commandId, e.message ?: "unknown")
                } else {
                    syncQueue.markFailed(command.commandId, "max retries exceeded: ${e.message}")
                    failed++
                }
            }
        }
        return SyncResult(succeeded, failed)
    }

    private suspend fun processAudioUpload(payload: Map<String, String>) {
        val observationId = payload["observationId"]!!
        val localFilePath = payload["localFilePath"]!!
        val checksum = payload["checksum"]!!

        val presignedResponse = network.post(
            "/api/v1/audio/presigned-url",
            mapOf("observation_id" to observationId, "checksum" to checksum),
        )
        val uploadUrl = presignedResponse["upload_url"] as String
        val uploadId  = presignedResponse["upload_id"] as String

        network.putBinary(uploadUrl, localFilePath)
        network.post("/api/v1/audio/confirm/$uploadId", mapOf("checksum" to checksum))
    }

    private fun exponentialBackoffMs(retryCount: Int): Long =
        (1_000L * (1 shl retryCount)).coerceAtMost(32_000L)
}

data class SyncResult(val succeeded: Int, val failed: Int)
