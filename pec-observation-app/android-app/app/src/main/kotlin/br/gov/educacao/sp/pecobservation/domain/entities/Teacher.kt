package br.gov.educacao.sp.pecobservation.domain.entities

import java.time.Instant
import java.util.UUID

data class Teacher(
    val id: UUID = UUID.randomUUID(),
    val schoolId: UUID,
    val fullName: String,
    val subjectArea: String,
    val createdAt: Instant = Instant.now(),
)
