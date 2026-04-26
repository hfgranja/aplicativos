package br.gov.educacao.sp.pecobservation.adapters.persistence

import br.gov.educacao.sp.pecobservation.adapters.persistence.entities.ObservationEntity
import br.gov.educacao.sp.pecobservation.adapters.persistence.entities.SchoolEntity
import br.gov.educacao.sp.pecobservation.adapters.persistence.entities.SyncCommandEntity
import br.gov.educacao.sp.pecobservation.adapters.persistence.entities.TeacherEntity
import br.gov.educacao.sp.pecobservation.domain.entities.Observation
import br.gov.educacao.sp.pecobservation.domain.entities.ObservationStatus
import br.gov.educacao.sp.pecobservation.domain.entities.School
import br.gov.educacao.sp.pecobservation.domain.entities.SyncCommand
import br.gov.educacao.sp.pecobservation.domain.entities.SyncStatus
import br.gov.educacao.sp.pecobservation.domain.entities.Teacher
import br.gov.educacao.sp.pecobservation.ports.ObservationRepositoryPort
import br.gov.educacao.sp.pecobservation.ports.SchoolRepositoryPort
import br.gov.educacao.sp.pecobservation.ports.SyncQueuePort
import br.gov.educacao.sp.pecobservation.ports.TeacherRepositoryPort
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import java.util.UUID
import javax.inject.Inject

class RoomObservationRepository @Inject constructor(
    private val dao: ObservationDao,
) : ObservationRepositoryPort {
    override fun observeAll(): Flow<List<Observation>> =
        dao.observeAll().map { list -> list.map { it.toDomain() } }

    override suspend fun save(observation: Observation) =
        dao.upsert(ObservationEntity.from(observation))

    override suspend fun fetchById(id: UUID): Observation? =
        dao.findById(id.toString())?.toDomain()

    override suspend fun fetchByStatus(status: ObservationStatus): List<Observation> =
        dao.findByStatus(status.name).map { it.toDomain() }

    override suspend fun delete(id: UUID) =
        dao.delete(id.toString())
}

class RoomSchoolRepository @Inject constructor(
    private val dao: SchoolDao,
) : SchoolRepositoryPort {
    override fun observeAll(): Flow<List<School>> =
        dao.observeAll().map { it.map { e -> e.toDomain() } }

    override suspend fun save(school: School) =
        dao.upsert(SchoolEntity.from(school))

    override suspend fun fetchById(id: UUID): School? =
        dao.findById(id.toString())?.toDomain()
}

class RoomTeacherRepository @Inject constructor(
    private val dao: TeacherDao,
) : TeacherRepositoryPort {
    override fun observeBySchool(schoolId: UUID): Flow<List<Teacher>> =
        dao.observeBySchool(schoolId.toString()).map { it.map { e -> e.toDomain() } }

    override suspend fun save(teacher: Teacher) =
        dao.upsert(TeacherEntity.from(teacher))

    override suspend fun fetchById(id: UUID): Teacher? =
        dao.findById(id.toString())?.toDomain()
}

class RoomSyncQueue @Inject constructor(
    private val dao: SyncCommandDao,
) : SyncQueuePort {
    override suspend fun enqueue(command: SyncCommand) =
        dao.upsert(SyncCommandEntity.from(command))

    override suspend fun pendingCommands(): List<SyncCommand> =
        dao.findPending().map { it.toDomain() }

    override suspend fun markInProgress(commandId: UUID) =
        dao.updateStatus(commandId.toString(), SyncStatus.IN_PROGRESS.name)

    override suspend fun markCompleted(commandId: UUID) =
        dao.updateStatus(commandId.toString(), SyncStatus.COMPLETED.name)

    override suspend fun markFailed(commandId: UUID, reason: String) =
        dao.markFailed(commandId.toString(), reason)

    override suspend fun pendingCount(): Int =
        dao.countPending()
}
