package br.gov.educacao.sp.pecobservation.adapters.ui.screens.recording

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import br.gov.educacao.sp.pecobservation.adapters.ui.viewmodels.RecordingViewModel
import br.gov.educacao.sp.pecobservation.ports.RecordingState
import java.util.UUID

@Composable
fun RecordingScreen(
    observationId: UUID,
    onDone: () -> Unit = {},
    vm: RecordingViewModel = hiltViewModel(),
) {
    val state   by vm.state.collectAsStateWithLifecycle()
    val elapsed by vm.elapsedSeconds.collectAsStateWithLifecycle()

    Scaffold(topBar = { TopAppBar(title = { Text("Gravar Aula") }) }) { padding ->
        Column(
            modifier              = Modifier.fillMaxSize().padding(padding).padding(24.dp),
            horizontalAlignment   = Alignment.CenterHorizontally,
            verticalArrangement   = Arrangement.SpaceEvenly,
        ) {
            // Status icon
            val (icon, tint) = when (state) {
                RecordingState.RECORDING -> Icons.Default.Mic  to Color(0xFFE53935)
                RecordingState.PAUSED    -> Icons.Default.Pause to Color(0xFFFFA000)
                RecordingState.COMPLETED -> Icons.Default.Stop  to Color(0xFF43A047)
                else                     -> Icons.Default.Mic  to Color(0xFF9E9E9E)
            }
            Icon(icon, contentDescription = null, tint = tint, modifier = Modifier.size(96.dp))

            // Timer
            Text(
                text       = vm.formattedElapsed(elapsed),
                fontSize   = 48.sp,
                fontFamily = FontFamily.Monospace,
                color      = if (state == RecordingState.RECORDING) Color(0xFFE53935)
                             else MaterialTheme.colorScheme.onBackground,
            )

            // Status label
            Text(
                text  = when (state) {
                    RecordingState.IDLE      -> "Pronto para gravar"
                    RecordingState.PREPARING -> "Preparando…"
                    RecordingState.RECORDING -> "Gravando"
                    RecordingState.PAUSED    -> "Pausado"
                    RecordingState.STOPPING  -> "Finalizando…"
                    RecordingState.COMPLETED -> "Gravação concluída"
                    RecordingState.FAILED    -> "Erro na gravação"
                },
                style = MaterialTheme.typography.titleMedium,
            )

            vm.error?.let {
                Text(it, color = MaterialTheme.colorScheme.error)
            }

            // Controls
            Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                when (state) {
                    RecordingState.IDLE, RecordingState.FAILED -> {
                        Button(onClick = { vm.startRecording(observationId) }) {
                            Icon(Icons.Default.Mic, null)
                            Spacer(Modifier.width(8.dp))
                            Text("Gravar")
                        }
                    }
                    RecordingState.RECORDING -> {
                        OutlinedButton(onClick = { vm.pauseRecording() }) {
                            Icon(Icons.Default.Pause, null); Spacer(Modifier.width(8.dp)); Text("Pausar")
                        }
                        Button(
                            onClick = { vm.stopRecording(observationId, onDone) },
                            colors  = ButtonDefaults.buttonColors(containerColor = Color(0xFFE53935)),
                        ) {
                            Icon(Icons.Default.Stop, null); Spacer(Modifier.width(8.dp)); Text("Parar")
                        }
                    }
                    RecordingState.PAUSED -> {
                        OutlinedButton(onClick = { vm.resumeRecording() }) {
                            Icon(Icons.Default.PlayArrow, null); Spacer(Modifier.width(8.dp)); Text("Retomar")
                        }
                        Button(
                            onClick = { vm.stopRecording(observationId, onDone) },
                            colors  = ButtonDefaults.buttonColors(containerColor = Color(0xFFE53935)),
                        ) {
                            Icon(Icons.Default.Stop, null); Spacer(Modifier.width(8.dp)); Text("Parar")
                        }
                    }
                    RecordingState.COMPLETED -> {
                        Button(onClick = onDone) { Text("Concluir") }
                    }
                    else -> {}
                }
            }
        }
    }
}
