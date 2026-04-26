package br.gov.educacao.sp.pecobservation.adapters.ui.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import br.gov.educacao.sp.pecobservation.domain.entities.School
import br.gov.educacao.sp.pecobservation.domain.entities.SyncCommand
import br.gov.educacao.sp.pecobservation.domain.entities.SyncCommandType
import br.gov.educacao.sp.pecobservation.ports.SchoolRepositoryPort
import br.gov.educacao.sp.pecobservation.ports.SyncQueuePort
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SchoolListViewModel @Inject constructor(
    private val repo: SchoolRepositoryPort,
    private val syncQueue: SyncQueuePort,
) : ViewModel() {

    val schools: StateFlow<List<School>> = repo.observeAll()
        .catch { emit(emptyList()) }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    fun addSchool(name: String, inepCode: String) {
        viewModelScope.launch {
            val school = School(name = name, inepCode = inepCode)
            repo.save(school)
            syncQueue.enqueue(
                SyncCommand(
                    type    = SyncCommandType.CREATE_SCHOOL,
                    payload = mapOf("schoolId" to school.id.toString(), "name" to name, "inepCode" to inepCode),
                )
            )
        }
    }
}
