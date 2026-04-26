package br.gov.educacao.sp.pecobservation.application

import br.gov.educacao.sp.pecobservation.application.usecases.CreateObservationInput
import br.gov.educacao.sp.pecobservation.application.usecases.CreateObservationUseCase
import br.gov.educacao.sp.pecobservation.domain.entities.Observation
import br.gov.educacao.sp.pecobservation.domain.entities.ObservationStatus
import br.gov.educacao.sp.pecobservation.domain.entities.SyncCommand
import br.gov.educacao.sp.pecobservation.domain.errors.DomainError
import br.gov.educacao.sp.pecobservation.ports.ObservationRepositoryPort
import br.gov.educacao.sp.pecobservation.ports.SyncQueuePort
import io.mockk.*
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.emptyFlow
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import java.util.UUID

class CreateObservationUseCaseTest {

    private val repo = FakeObservationRepository()
    private val queue = FakeSyncQueue()
    private lateinit var useCase: CreateObservationUseCase

    @Before
    fun setup() {
        useCase = CreateObservationUseCase(repo, queue)
    }

    @Test
    fun `creates observation with DRAFT status`() = runTest {
        val result = useCase.execute(validInput())
        assertEquals(ObservationStatus.DRAFT, result.status)
        assertEquals(1, repo.saved.size)
        assertEquals(1, queue.enqueued.size)
    }

    @Test(expected = DomainError.ValidationError::class)
    fun `throws when subject is blank`() = runTest {
        useCase.execute(validInput(subject = ""))
    }

    @Test(expected = DomainError.ValidationError::class)
    fun `throws when grade is blank`() = runTest {
        useCase.execute(validInput(grade = ""))
    }

    @Test(expected = DomainError.ValidationError::class)
    fun `throws when lessonTheme is blank`() = runTest {
        useCase.execute(validInput(lessonTheme = ""))
    }

    private fun validInput(
        subject     : String = "Matemática",
        grade       : String = "7º ano",
        lessonTheme : String = "Frações",
    ) = CreateObservationInput(
        schoolId        = UUID.randomUUID(),
        teacherId       = UUID.randomUUID(),
        subject         = subject,
        grade           = grade,
        lessonTheme     = lessonTheme,
    )
}

private class FakeObservationRepository : ObservationRepositoryPort {
    val saved = mutableListOf<Observation>()
    override fun observeAll(): Flow<List<Observation>> = emptyFlow()
    override suspend fun save(observation: Observation) { saved.add(observation) }
    override suspend fun fetchById(id: UUID): Observation? = saved.find { it.id == id }
    override suspend fun fetchByStatus(status: ObservationStatus) = saved.filter { it.status == status }
    override suspend fun delete(id: UUID) { saved.removeIf { it.id == id } }
}

private class FakeSyncQueue : SyncQueuePort {
    val enqueued = mutableListOf<SyncCommand>()
    override suspend fun enqueue(command: SyncCommand) { enqueued.add(command) }
    override suspend fun pendingCommands() = enqueued
    override suspend fun markInProgress(commandId: UUID) {}
    override suspend fun markCompleted(commandId: UUID) {}
    override suspend fun markFailed(commandId: UUID, reason: String) {}
    override suspend fun pendingCount() = enqueued.size
}
