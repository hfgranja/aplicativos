package br.gov.educacao.sp.pecobservation.adapters.ui.screens.sync

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CloudSync
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import br.gov.educacao.sp.pecobservation.adapters.ui.viewmodels.SyncStatusViewModel

@Composable
fun SyncStatusScreen(vm: SyncStatusViewModel = hiltViewModel()) {
    val pending   by vm.pendingCount.collectAsStateWithLifecycle()
    val isSyncing by vm.isSyncing.collectAsStateWithLifecycle()
    val result    by vm.lastResult.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        vm.refreshCount()
        vm.scheduleBackgroundSync()
    }

    Scaffold(topBar = { TopAppBar(title = { Text("Sincronização") }) }) { padding ->
        Column(
            modifier              = Modifier.fillMaxSize().padding(padding).padding(24.dp),
            horizontalAlignment   = Alignment.CenterHorizontally,
            verticalArrangement   = Arrangement.spacedBy(24.dp),
        ) {
            Icon(
                imageVector     = Icons.Default.CloudSync,
                contentDescription = null,
                modifier        = Modifier.size(72.dp),
                tint            = if (pending > 0) MaterialTheme.colorScheme.primary
                                  else MaterialTheme.colorScheme.outline,
            )

            Text(
                text  = if (pending == 0) "Tudo sincronizado"
                        else "$pending item(s) aguardando envio",
                style = MaterialTheme.typography.titleMedium,
            )

            result?.let {
                Card(modifier = Modifier.fillMaxWidth()) {
                    Text(it, modifier = Modifier.padding(16.dp))
                }
            }

            if (isSyncing) {
                CircularProgressIndicator()
            } else {
                Button(
                    onClick  = { vm.syncNow() },
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Icon(Icons.Default.CloudSync, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Sincronizar Agora")
                }
            }
        }
    }
}
