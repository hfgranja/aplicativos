package br.gov.educacao.sp.pecobservation.ports

import br.gov.educacao.sp.pecobservation.domain.entities.Observation
import br.gov.educacao.sp.pecobservation.domain.entities.ObservationStatus
import kotlinx.coroutines.flow.Flow
import java.util.UUID

interface ObservationRepositoryPort {
    fun observeAll(): Flow<List<Observation>>
    suspend fun save(observation: Observation)
    suspend fun fetchById(id: UUID): Observation?
    suspend fun fetchByStatus(status: ObservationStatus): List<Observation>
    suspend fun delete(id: UUID)
}
