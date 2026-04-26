package br.gov.educacao.sp.pecobservation.adapters.ui.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import br.gov.educacao.sp.pecobservation.application.usecases.CreateObservationInput
import br.gov.educacao.sp.pecobservation.application.usecases.CreateObservationUseCase
import br.gov.educacao.sp.pecobservation.domain.entities.Observation
import br.gov.educacao.sp.pecobservation.ports.ObservationRepositoryPort
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.util.UUID
import javax.inject.Inject

@HiltViewModel
class ObservationListViewModel @Inject constructor(
    private val repo: ObservationRepositoryPort,
    private val createUseCase: CreateObservationUseCase,
) : ViewModel() {

    val observations: StateFlow<List<Observation>> = repo.observeAll()
        .catch { emit(emptyList()) }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    var error: String? = null
        private set

    fun createObservation(
        schoolId: UUID,
        teacherId: UUID,
        subject: String,
        grade: String,
        lessonTheme: String,
        lessonObjectives: String = "",
        onSuccess: (Observation) -> Unit = {},
    ) {
        viewModelScope.launch {
            try {
                val obs = createUseCase.execute(
                    CreateObservationInput(schoolId, teacherId, subject, grade, lessonTheme, lessonObjectives)
                )
                error = null
                onSuccess(obs)
            } catch (e: Exception) {
                error = e.message
            }
        }
    }
}
