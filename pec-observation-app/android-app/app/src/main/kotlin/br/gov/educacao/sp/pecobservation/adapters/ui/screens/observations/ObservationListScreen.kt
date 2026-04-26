package br.gov.educacao.sp.pecobservation.adapters.ui.screens.observations

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavController
import br.gov.educacao.sp.pecobservation.adapters.ui.viewmodels.ObservationListViewModel
import br.gov.educacao.sp.pecobservation.domain.entities.Observation
import br.gov.educacao.sp.pecobservation.domain.entities.ObservationStatus
import java.util.UUID

@Composable
fun ObservationListScreen(
    navController: NavController,
    vm: ObservationListViewModel = hiltViewModel(),
) {
    val observations by vm.observations.collectAsStateWithLifecycle()
    var showNewSheet by remember { mutableStateOf(false) }

    Scaffold(
        topBar = { TopAppBar(title = { Text("Observações") }) },
        floatingActionButton = {
            FloatingActionButton(onClick = { showNewSheet = true }) {
                Icon(Icons.Default.Add, contentDescription = "Nova observação")
            }
        },
    ) { padding ->
        if (observations.isEmpty()) {
            Box(Modifier.fillMaxSize().padding(padding), contentAlignment = Alignment.Center) {
                Text("Nenhuma observação registrada", style = MaterialTheme.typography.bodyLarge)
            }
        } else {
            LazyColumn(contentPadding = padding) {
                items(observations, key = { it.id.toString() }) { obs ->
                    ObservationCard(obs) {
                        navController.navigate("recording/${obs.id}")
                    }
                    HorizontalDivider()
                }
            }
        }
    }

    if (showNewSheet) {
        NewObservationSheet(
            onDismiss = { showNewSheet = false },
            onCreate  = { schoolId, teacherId, subject, grade, theme ->
                vm.createObservation(schoolId, teacherId, subject, grade, theme)
                showNewSheet = false
            },
        )
    }
}

@Composable
private fun ObservationCard(obs: Observation, onClick: () -> Unit) {
    ListItem(
        modifier         = Modifier.clickable(onClick = onClick),
        headlineContent  = { Text("${obs.subject} — ${obs.grade}") },
        supportingContent = { Text(obs.lessonTheme, maxLines = 1) },
        trailingContent  = { StatusChip(obs.status) },
    )
}

@Composable
private fun StatusChip(status: ObservationStatus) {
    val color = when (status) {
        ObservationStatus.DRAFT              -> Color(0xFF9E9E9E)
        ObservationStatus.READY_TO_RECORD    -> Color(0xFF1976D2)
        ObservationStatus.RECORDED           -> Color(0xFF388E3C)
        ObservationStatus.AUDIO_UPLOADED     -> Color(0xFF0097A7)
        ObservationStatus.TRANSCRIBING       -> Color(0xFFF57C00)
        ObservationStatus.TRANSCRIBED        -> Color(0xFF7B1FA2)
        ObservationStatus.GENERATING_FEEDBACK-> Color(0xFFE64A19)
        ObservationStatus.FEEDBACK_READY     -> Color(0xFF00796B)
        ObservationStatus.IN_REVIEW          -> Color(0xFF5D4037)
        ObservationStatus.HUMAN_REVIEWED     -> Color(0xFF303F9F)
        ObservationStatus.APPROVED           -> Color(0xFF2E7D32)
    }
    Surface(shape = MaterialTheme.shapes.small, color = color.copy(alpha = 0.12f)) {
        Text(
            text     = status.displayName,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
            style    = MaterialTheme.typography.labelSmall,
            color    = color,
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun NewObservationSheet(
    onDismiss: () -> Unit,
    onCreate: (UUID, UUID, String, String, String) -> Unit,
) {
    var subject by remember { mutableStateOf("") }
    var grade   by remember { mutableStateOf("") }
    var theme   by remember { mutableStateOf("") }
    val placeholderSchoolId  = UUID.fromString("00000000-0000-0000-0000-000000000001")
    val placeholderTeacherId = UUID.fromString("00000000-0000-0000-0000-000000000002")

    ModalBottomSheet(onDismissRequest = onDismiss) {
        Column(
            modifier              = Modifier.padding(24.dp).fillMaxWidth(),
            verticalArrangement   = Arrangement.spacedBy(16.dp),
        ) {
            Text("Nova Observação", style = MaterialTheme.typography.titleLarge)
            OutlinedTextField(value = subject, onValueChange = { subject = it },
                label = { Text("Disciplina") }, modifier = Modifier.fillMaxWidth())
            OutlinedTextField(value = grade, onValueChange = { grade = it },
                label = { Text("Turma") }, modifier = Modifier.fillMaxWidth())
            OutlinedTextField(value = theme, onValueChange = { theme = it },
                label = { Text("Tema da Aula") }, modifier = Modifier.fillMaxWidth())
            Button(
                onClick  = { onCreate(placeholderSchoolId, placeholderTeacherId, subject, grade, theme) },
                enabled  = subject.isNotBlank() && grade.isNotBlank() && theme.isNotBlank(),
                modifier = Modifier.fillMaxWidth(),
            ) { Text("Criar") }
            Spacer(Modifier.height(16.dp))
        }
    }
}
