package br.gov.educacao.sp.pecobservation.adapters.ui.screens.bestpractices

import android.net.Uri
import android.widget.VideoView
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
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import br.gov.educacao.sp.pecobservation.adapters.ui.viewmodels.BestPracticesViewModel
import br.gov.educacao.sp.pecobservation.domain.entities.BestPracticeCard
import kotlinx.coroutines.launch

@Composable
fun BestPracticesScreen(vm: BestPracticesViewModel = hiltViewModel()) {
    val cards     by vm.cards.collectAsStateWithLifecycle()
    val isLoading by vm.isLoading.collectAsStateWithLifecycle()

    val scope          = rememberCoroutineScope()
    var selectedStatus by remember { mutableStateOf("published") }
    var detailCard     by remember { mutableStateOf<BestPracticeCard?>(null) }
    var showDistribute by remember { mutableStateOf<BestPracticeCard?>(null) }
    var videoUrl       by remember { mutableStateOf<String?>(null) }
    var videoLoading   by remember { mutableStateOf(false) }

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
            card         = card,
            videoLoading = videoLoading,
            onDismiss    = { detailCard = null },
            onDistribute = { showDistribute = card; detailCard = null },
            onPublish    = { vm.publish(card.id, card.title); detailCard = null },
            onWatchVideo = {
                videoLoading = true
                scope.launch {
                    videoUrl = vm.fetchVideoUrl(card.id)
                    videoLoading = false
                }
            },
        )
    }

    videoUrl?.let { url ->
        VideoPlayerDialog(url = url, onDismiss = { videoUrl = null })
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
    card:         BestPracticeCard,
    videoLoading: Boolean,
    onDismiss:    () -> Unit,
    onDistribute: () -> Unit,
    onPublish:    () -> Unit,
    onWatchVideo: () -> Unit,
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

                // Video section
                Divider()
                when (card.videoStatus) {
                    "ready" -> {
                        Button(
                            onClick  = onWatchVideo,
                            enabled  = !videoLoading,
                            modifier = Modifier.fillMaxWidth(),
                            colors   = ButtonDefaults.buttonColors(
                                containerColor = MaterialTheme.colorScheme.tertiary,
                            ),
                        ) {
                            if (videoLoading) {
                                CircularProgressIndicator(
                                    modifier = Modifier.size(16.dp),
                                    strokeWidth = 2.dp,
                                    color = MaterialTheme.colorScheme.onTertiary,
                                )
                                Spacer(Modifier.width(8.dp))
                            } else {
                                Icon(Icons.Default.PlayArrow, contentDescription = null,
                                    modifier = Modifier.size(18.dp))
                                Spacer(Modifier.width(4.dp))
                            }
                            Text("Assistir vídeo anime")
                        }
                        card.videoDurationS?.let { dur ->
                            Text(
                                "Duração: ${dur / 60}m ${dur % 60}s",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                    "processing" -> Row(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalAlignment     = Alignment.CenterVertically,
                    ) {
                        CircularProgressIndicator(modifier = Modifier.size(14.dp), strokeWidth = 2.dp)
                        Text("Gerando vídeo…", style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    "failed" -> Text("⚠️ Falha na geração do vídeo",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.error)
                    else -> Text("🎬 Vídeo será gerado em breve",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
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
private fun VideoPlayerDialog(url: String, onDismiss: () -> Unit) {
    Dialog(
        onDismissRequest = onDismiss,
        properties       = DialogProperties(usePlatformDefaultWidth = false),
    ) {
        Box(
            Modifier
                .fillMaxWidth()
                .aspectRatio(16f / 9f)
        ) {
            AndroidView(
                factory  = { ctx ->
                    VideoView(ctx).apply {
                        setVideoURI(Uri.parse(url))
                        setOnPreparedListener { mp -> mp.start() }
                    }
                },
                modifier = Modifier.fillMaxSize(),
            )
            IconButton(
                onClick  = onDismiss,
                modifier = Modifier.align(Alignment.TopEnd).padding(4.dp),
            ) {
                Icon(Icons.Default.Close, contentDescription = "Fechar",
                    tint = androidx.compose.ui.graphics.Color.White)
            }
        }
    }
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
