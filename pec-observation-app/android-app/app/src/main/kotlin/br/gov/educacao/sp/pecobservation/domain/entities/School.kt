package br.gov.educacao.sp.pecobservation.domain.entities

import java.time.Instant
import java.util.UUID

data class School(
    val id: UUID = UUID.randomUUID(),
    val name: String,
    val inepCode: String,
    val address: String = "",
    val city: String = "",
    val createdAt: Instant = Instant.now(),
)
