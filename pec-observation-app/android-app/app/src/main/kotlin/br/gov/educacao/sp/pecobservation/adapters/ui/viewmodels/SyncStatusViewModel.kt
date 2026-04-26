package br.gov.educacao.sp.pecobservation.adapters.ui.viewmodels

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import br.gov.educacao.sp.pecobservation.adapters.sync.SyncWorker
import br.gov.educacao.sp.pecobservation.application.usecases.SyncUseCase
import br.gov.educacao.sp.pecobservation.ports.SyncQueuePort
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SyncStatusViewModel @Inject constructor(
    private val syncQueue: SyncQueuePort,
    private val syncUseCase: SyncUseCase,
    @ApplicationContext private val context: Context,
) : ViewModel() {

    private val _pendingCount = MutableStateFlow(0)
    val pendingCount: StateFlow<Int> = _pendingCount.asStateFlow()

    private val _isSyncing = MutableStateFlow(false)
    val isSyncing: StateFlow<Boolean> = _isSyncing.asStateFlow()

    private val _lastResult = MutableStateFlow<String?>(null)
    val lastResult: StateFlow<String?> = _lastResult.asStateFlow()

    init { refreshCount() }

    fun refreshCount() {
        viewModelScope.launch {
            _pendingCount.value = syncQueue.pendingCount()
        }
    }

    fun syncNow() {
        if (_isSyncing.value) return
        viewModelScope.launch {
            _isSyncing.value = true
            try {
                val result = syncUseCase.execute()
                _lastResult.value = "Sincronizado: ${result.succeeded} ok, ${result.failed} falhas"
            } catch (e: Exception) {
                _lastResult.value = "Erro: ${e.message}"
            } finally {
                _isSyncing.value = false
                refreshCount()
            }
        }
    }

    fun scheduleBackgroundSync() {
        SyncWorker.schedule(context)
    }
}
