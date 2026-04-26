package br.gov.educacao.sp.pecobservation.domain

import br.gov.educacao.sp.pecobservation.domain.entities.ObservationStatus
import org.junit.Assert.*
import org.junit.Test

class ObservationStatusTest {

    @Test
    fun `all statuses have non-empty display names`() {
        ObservationStatus.entries.forEach { status ->
            assertTrue("${status.name} should have a displayName", status.displayName.isNotBlank())
        }
    }

    @Test
    fun `fromRaw round-trips for all statuses`() {
        ObservationStatus.entries.forEach { status ->
            assertEquals(status, ObservationStatus.fromRaw(status.name))
        }
    }

    @Test
    fun `fromRaw unknown value returns DRAFT`() {
        assertEquals(ObservationStatus.DRAFT, ObservationStatus.fromRaw("UNKNOWN_VALUE"))
    }

    @Test
    fun `observation isReadyForRecording when fields filled`() {
        val obs = br.gov.educacao.sp.pecobservation.domain.entities.Observation(
            schoolId    = java.util.UUID.randomUUID(),
            teacherId   = java.util.UUID.randomUUID(),
            subject     = "Matemática",
            grade       = "7º ano",
            lessonTheme = "Frações",
        )
        assertTrue(obs.isReadyForRecording)
    }

    @Test
    fun `observation not ready when subject empty`() {
        val obs = br.gov.educacao.sp.pecobservation.domain.entities.Observation(
            schoolId    = java.util.UUID.randomUUID(),
            teacherId   = java.util.UUID.randomUUID(),
            subject     = "",
            grade       = "7º ano",
            lessonTheme = "Frações",
        )
        assertFalse(obs.isReadyForRecording)
    }
}
