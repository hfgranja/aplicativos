package br.gov.educacao.sp.pecobservation.adapters.persistence.entities

import androidx.room.Entity
import androidx.room.PrimaryKey
import br.gov.educacao.sp.pecobservation.domain.entities.AudioRecordingResult
import br.gov.educacao.sp.pecobservation.domain.entities.Observation
import br.gov.educacao.sp.pecobservation.domain.entities.ObservationStatus
import java.time.Instant
import java.util.UUID

@Entity(tableName = "observations")
data class ObservationEntity(
    @PrimaryKey val id: String,
    val schoolId: String,
    val teacherId: String,
    val subject: String,
    val grade: String,
    val lessonTheme: String,
    val lessonObjectives: String,
    val statusRaw: String,
    val audioFilePath: String?,
    val audioDurationSeconds: Int?,
    val audioFileSizeBytes: Long?,
    val audioChecksum: String?,
    val transcription: String?,
    val createdAt: Long,
    val updatedAt: Long,
) {
    fun toDomain(): Observation = Observation(
        id               = UUID.fromString(id),
        schoolId         = UUID.fromString(schoolId),
        teacherId        = UUID.fromString(teacherId),
        subject          = subject,
        grade            = grade,
        lessonTheme      = lessonTheme,
        lessonObjectives = lessonObjectives,
        status           = ObservationStatus.fromRaw(statusRaw),
        audioRecording   = if (audioFilePath != null) AudioRecordingResult(
            observationId  = UUID.fromString(id),
            localFilePath  = audioFilePath,
            durationSeconds = audioDurationSeconds ?: 0,
            fileSizeBytes  = audioFileSizeBytes ?: 0,
            checksum       = audioChecksum ?: "",
        ) else null,
        transcription    = transcription,
        createdAt        = Instant.ofEpochMilli(createdAt),
        updatedAt        = Instant.ofEpochMilli(updatedAt),
    )

    companion object {
        fun from(obs: Observation) = ObservationEntity(
            id                  = obs.id.toString(),
            schoolId            = obs.schoolId.toString(),
            teacherId           = obs.teacherId.toString(),
            subject             = obs.subject,
            grade               = obs.grade,
            lessonTheme         = obs.lessonTheme,
            lessonObjectives    = obs.lessonObjectives,
            statusRaw           = obs.status.name,
            audioFilePath       = obs.audioRecording?.localFilePath,
            audioDurationSeconds = obs.audioRecording?.durationSeconds,
            audioFileSizeBytes  = obs.audioRecording?.fileSizeBytes,
            audioChecksum       = obs.audioRecording?.checksum,
            transcription       = obs.transcription,
            createdAt           = obs.createdAt.toEpochMilli(),
            updatedAt           = obs.updatedAt.toEpochMilli(),
        )
    }
}
