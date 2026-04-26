package br.gov.educacao.sp.pecobservation.adapters.ui.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import br.gov.educacao.sp.pecobservation.application.usecases.RecordAudioUseCase
import br.gov.educacao.sp.pecobservation.ports.AudioRecordingPort
import br.gov.educacao.sp.pecobservation.ports.RecordingState
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.util.UUID
import javax.inject.Inject

@HiltViewModel
class RecordingViewModel @Inject constructor(
    private val recorder: AudioRecordingPort,
    private val useCase: RecordAudioUseCase,
) : ViewModel() {

    val state: StateFlow<RecordingState> = recorder.state
        .stateIn(viewModelScope, SharingStarted.Eagerly, RecordingState.IDLE)

    val elapsedSeconds: StateFlow<Int> = recorder.elapsedSeconds
        .stateIn(viewModelScope, SharingStarted.Eagerly, 0)

    var error: String? = null
        private set

    fun startRecording(observationId: UUID) {
        viewModelScope.launch {
            try {
                useCase.startRecording(observationId)
                error = null
            } catch (e: Exception) {
                error = e.message
            }
        }
    }

    fun pauseRecording() {
        viewModelScope.launch { recorder.pauseRecording() }
    }

    fun resumeRecording() {
        viewModelScope.launch { recorder.resumeRecording() }
    }

    fun stopRecording(observationId: UUID, onDone: () -> Unit = {}) {
        viewModelScope.launch {
            try {
                useCase.stopAndSave(observationId)
                error = null
                onDone()
            } catch (e: Exception) {
                error = e.message
            }
        }
    }

    fun cancelRecording() {
        recorder.cancelRecording()
    }

    fun formattedElapsed(seconds: Int): String {
        val m = seconds / 60
        val s = seconds % 60
        return "%02d:%02d".format(m, s)
    }
}
