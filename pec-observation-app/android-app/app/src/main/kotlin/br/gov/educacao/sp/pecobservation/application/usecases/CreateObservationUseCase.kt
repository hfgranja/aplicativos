package br.gov.educacao.sp.pecobservation.application.usecases

import br.gov.educacao.sp.pecobservation.domain.entities.Observation
import br.gov.educacao.sp.pecobservation.domain.entities.SyncCommand
import br.gov.educacao.sp.pecobservation.domain.entities.SyncCommandType
import br.gov.educacao.sp.pecobservation.domain.errors.DomainError
import br.gov.educacao.sp.pecobservation.ports.ObservationRepositoryPort
import br.gov.educacao.sp.pecobservation.ports.SyncQueuePort
import java.util.UUID
import javax.inject.Inject

data class CreateObservationInput(
    val schoolId: UUID,
    val teacherId: UUID,
    val subject: String,
    val grade: String,
    val lessonTheme: String,
    val lessonObjectives: String = "",
)

class CreateObservationUseCase @Inject constructor(
    private val repo: ObservationRepositoryPort,
    private val syncQueue: SyncQueuePort,
) {
    suspend fun execute(input: CreateObservationInput): Observation {
        if (input.subject.isBlank())
            throw DomainError.ValidationError("subject", "cannot be empty")
        if (input.grade.isBlank())
            throw DomainError.ValidationError("grade", "cannot be empty")
        if (input.lessonTheme.isBlank())
            throw DomainError.ValidationError("lessonTheme", "cannot be empty")

        val observation = Observation(
            schoolId        = input.schoolId,
            teacherId       = input.teacherId,
            subject         = input.subject,
            grade           = input.grade,
            lessonTheme     = input.lessonTheme,
            lessonObjectives = input.lessonObjectives,
        )

        repo.save(observation)
        syncQueue.enqueue(
            SyncCommand(
                type    = SyncCommandType.CREATE_OBSERVATION,
                payload = mapOf("observationId" to observation.id.toString()),
            )
        )
        return observation
    }
}
