package br.gov.educacao.sp.pecobservation.application.usecases

import br.gov.educacao.sp.pecobservation.domain.entities.ObservationStatus
import br.gov.educacao.sp.pecobservation.domain.entities.SyncCommand
import br.gov.educacao.sp.pecobservation.domain.entities.SyncCommandType
import br.gov.educacao.sp.pecobservation.domain.errors.DomainError
import br.gov.educacao.sp.pecobservation.domain.errors.RecordingError
import br.gov.educacao.sp.pecobservation.ports.AudioRecordingPort
import br.gov.educacao.sp.pecobservation.ports.ObservationRepositoryPort
import br.gov.educacao.sp.pecobservation.ports.SyncQueuePort
import java.time.Instant
import java.util.UUID
import javax.inject.Inject

class RecordAudioUseCase @Inject constructor(
    private val recorder: AudioRecordingPort,
    private val repo: ObservationRepositoryPort,
    private val syncQueue: SyncQueuePort,
) {
    suspend fun startRecording(observationId: UUID) {
        val obs = repo.fetchById(observationId)
            ?: throw DomainError.NotFound("Observation", observationId.toString())

        if (!obs.isReadyForRecording)
            throw DomainError.ValidationError("observation", "not ready for recording")

        val permitted = recorder.requestPermission()
        if (!permitted) throw RecordingError.PermissionDenied()

        recorder.startRecording(observationId)
    }

    suspend fun stopAndSave(observationId: UUID) {
        val result = recorder.stopRecording()
        val obs = repo.fetchById(observationId)
            ?: throw DomainError.NotFound("Observation", observationId.toString())

        val updated = obs.copy(
            status         = ObservationStatus.RECORDED,
            audioRecording = result,
            updatedAt      = Instant.now(),
        )
        repo.save(updated)

        syncQueue.enqueue(
            SyncCommand(
                type = SyncCommandType.UPLOAD_AUDIO,
                payload = mapOf(
                    "observationId" to observationId.toString(),
                    "localFilePath" to result.localFilePath,
                    "checksum"      to result.checksum,
                    "durationSec"   to result.durationSeconds.toString(),
                    "fileSizeBytes" to result.fileSizeBytes.toString(),
                ),
            )
        )
    }
}
