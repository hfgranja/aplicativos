package br.gov.educacao.sp.pecobservation.ports

import br.gov.educacao.sp.pecobservation.domain.entities.AudioRecordingResult
import kotlinx.coroutines.flow.StateFlow
import java.util.UUID

enum class RecordingState {
    IDLE, PREPARING, RECORDING, PAUSED, STOPPING, COMPLETED, FAILED
}

interface AudioRecordingPort {
    val state: StateFlow<RecordingState>
    val elapsedSeconds: StateFlow<Int>

    suspend fun requestPermission(): Boolean
    suspend fun startRecording(observationId: UUID)
    suspend fun pauseRecording()
    suspend fun resumeRecording()
    suspend fun stopRecording(): AudioRecordingResult
    fun cancelRecording()
}
