package br.gov.educacao.sp.pecobservation.domain.entities

import java.time.Instant
import java.util.UUID

enum class ObservationStatus(val displayName: String) {
    DRAFT("Rascunho"),
    READY_TO_RECORD("Pronto para Gravar"),
    RECORDED("Gravado"),
    AUDIO_UPLOADED("Áudio Enviado"),
    TRANSCRIBING("Transcrevendo"),
    TRANSCRIBED("Transcrito"),
    GENERATING_FEEDBACK("Gerando Feedback"),
    FEEDBACK_READY("Feedback Disponível"),
    IN_REVIEW("Em Revisão"),
    HUMAN_REVIEWED("Revisado"),
    APPROVED("Aprovado");

    companion object {
        fun fromRaw(raw: String): ObservationStatus =
            entries.firstOrNull { it.name == raw } ?: DRAFT
    }
}

data class AudioRecordingResult(
    val observationId: UUID,
    val localFilePath: String,
    val durationSeconds: Int,
    val fileSizeBytes: Long,
    val checksum: String,
    val codec: String = "aac",
)

data class Observation(
    val id: UUID = UUID.randomUUID(),
    val schoolId: UUID,
    val teacherId: UUID,
    val subject: String,
    val grade: String,
    val lessonTheme: String,
    val lessonObjectives: String = "",
    val status: ObservationStatus = ObservationStatus.DRAFT,
    val audioRecording: AudioRecordingResult? = null,
    val transcription: String? = null,
    val createdAt: Instant = Instant.now(),
    val updatedAt: Instant = Instant.now(),
) {
    val isReadyForRecording: Boolean
        get() = subject.isNotBlank() && grade.isNotBlank() && lessonTheme.isNotBlank()
}
