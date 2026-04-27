package br.gov.educacao.sp.pecobservation.adapters.ui.screens.bestpractices

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import br.gov.educacao.sp.pecobservation.adapters.ui.viewmodels.BestPracticesViewModel
import br.gov.educacao.sp.pecobservation.domain.entities.BestPracticeCard

@Composable
fun BestPracticesScreen(vm: BestPracticesViewModel = hiltViewModel()) {
    val cards     by vm.cards.collectAsStateWithLifecycle()
    val isLoading by vm.isLoading.collectAsStateWithLifecycle()

    var selectedStatus by remember { mutableStateOf("published") }
    var detailCard     by remember { mutableStateOf<BestPracticeCard?>(null) }
    var showDistribute by remember { mutableStateOf<BestPracticeCard?>(null) }

    LaunchedEffect(selectedStatus) { vm.loadLibrary(selectedStatus) }

    Scaffold(
        topBar = { TopAppBar(title = { Text("Boas Práticas") }) }
    ) { padding ->
        Column(Modifier.padding(padding)) {
            TabRow(selectedTabIndex = if (selectedStatus == "published") 0 else 1) {
                Tab(selected = selectedStatus == "published",
                    onClick  = { selectedStatus = "published" },
                    text     = { Text("Biblioteca") })
                Tab(selected = selectedStatus == "draft",
                    onClick  = { selectedStatus = "draft" },
                    text     = { Text("Rascunhos") })
            }

            if (isLoading) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            } else if (cards.isEmpty()) {
                EmptyPractices(selectedStatus)
            } else {
                LazyColumn(
                    contentPadding = PaddingValues(12.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    item {
                        InfoBanner()
                    }
                    items(cards, key = { it.id }) { card ->
                        PracticeCardItem(
                            card      = card,
                            onClick   = { detailCard = card },
                            onPublish = { vm.publish(card.id, card.title) },
                            onDistribute = { showDistribute = card },
                        )
                    }
                }
            }
        }
    }

    detailCard?.let { card ->
        PracticeDetailDialog(
            card        = card,
            onDismiss   = { detailCard = null },
            onDistribute = { showDistribute = card; detailCard = null },
            onPublish   = { vm.publish(card.id, card.title); detailCard = null },
        )
    }

    showDistribute?.let { card ->
        DistributeDialog(
            card      = card,
            onDismiss = { showDistribute = null },
            onSend    = { teacherIds, message ->
                vm.distribute(card.id, teacherIds, message)
                showDistribute = null
            },
        )
    }
}

@Composable
private fun InfoBanner() {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(bottom = 4.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text("✨", style = MaterialTheme.typography.bodyLarge)
        Text(
            "Momentos exemplares extraídos automaticamente e anonimizados.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun PracticeCardItem(
    card: BestPracticeCard,
    onClick: () -> Unit,
    onPublish: () -> Unit,
    onDistribute: () -> Unit,
) {
    Card(
        onClick   = onClick,
        modifier  = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment     = Alignment.CenterVertically,
            ) {
                val criterion = card.criterionEnum
                Text(criterion?.emoji ?: "📚", style = MaterialTheme.typography.titleMedium)
                Column(Modifier.weight(1f)) {
                    Text(card.title, style = MaterialTheme.typography.titleSmall)
                    Text(
                        criterion?.displayName ?: card.criterion,
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.primary,
                    )
                }
                if (card.hasAudio) {
                    Icon(Icons.Default.Mic, "Áudio", tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.size(18.dp))
                }
            }

            Text(
                card.excerpt,
                style     = MaterialTheme.typography.bodySmall,
                fontStyle = FontStyle.Italic,
                maxLines  = 2,
                color     = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                SuggestionChip(onClick = {}, label = { Text(card.subject, style = MaterialTheme.typography.labelSmall) })
                SuggestionChip(onClick = {}, label = { Text(card.grade, style = MaterialTheme.typography.labelSmall) })
            }

            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                if (card.status == "draft") {
                    TextButton(onClick = onPublish) { Text("Publicar") }
                } else if (card.status == "published") {
                    TextButton(onClick = onDistribute) {
                        Icon(Icons.Default.Send, contentDescription = null,
                            modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(4.dp))
                        Text("Enviar")
                    }
                }
            }
        }
    }
}

@Composable
private fun PracticeDetailDialog(
    card: BestPracticeCard,
    onDismiss: () -> Unit,
    onDistribute: () -> Unit,
    onPublish: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title   = { Text(card.title) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("Trecho (anonimizado):", style = MaterialTheme.typography.labelMedium)
                Text(
                    card.excerpt,
                    fontStyle = FontStyle.Italic,
                    style     = MaterialTheme.typography.bodySmall,
                    modifier  = Modifier.padding(start = 8.dp),
                )
                Divider()
                Text("Por que é uma boa prática:", style = MaterialTheme.typography.labelMedium)
                Text(card.aiExplanation, style = MaterialTheme.typography.bodySmall)
                if (card.rubricAlignment.isNotEmpty()) {
                    Divider()
                    Text("Alinhamento SEDUC:", style = MaterialTheme.typography.labelMedium)
                    card.rubricAlignment.forEach { item ->
                        Row {
                            Text("✓ ", color = MaterialTheme.colorScheme.primary)
                            Text(item, style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
            }
        },
        confirmButton = {
            if (card.status == "published")
                TextButton(onClick = { onDistribute() }) { Text("Enviar") }
            else
                TextButton(onClick = { onPublish() }) { Text("Publicar") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Fechar") } },
    )
}

@Composable
private fun DistributeDialog(
    card:     BestPracticeCard,
    onDismiss: () -> Unit,
    onSend:   (List<String>, String) -> Unit,
) {
    var teacherIds by remember { mutableStateOf("") }
    var message    by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title   = { Text("Enviar para Professores") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("\"${card.title}\"", style = MaterialTheme.typography.bodySmall,
                    fontStyle = FontStyle.Italic)
                OutlinedTextField(
                    value = teacherIds, onValueChange = { teacherIds = it },
                    label = { Text("IDs dos professores (separados por vírgula)") },
                    modifier = Modifier.fillMaxWidth(),
                )
                OutlinedTextField(
                    value = message, onValueChange = { message = it },
                    label = { Text("Mensagem opcional") },
                    modifier = Modifier.fillMaxWidth(), minLines = 2,
                )
                Text(
                    "⚠️ O conteúdo é totalmente anonimizado antes do envio.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick  = {
                    val ids = teacherIds.split(",").map { it.trim() }.filter { it.isNotBlank() }
                    onSend(ids, message)
                },
                enabled  = teacherIds.isNotBlank(),
            ) { Text("Enviar") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancelar") } },
    )
}

@Composable
private fun EmptyPractices(status: String) {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("⭐", style = MaterialTheme.typography.displaySmall)
            Text(
                if (status == "draft") "Nenhum rascunho pendente"
                else "Biblioteca vazia — aguarde novas observações",
                style = MaterialTheme.typography.bodyLarge,
            )
            Text(
                "Boas práticas são extraídas automaticamente quando uma observação é aprovada.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(horizontal = 32.dp),
            )
        }
    }
}
