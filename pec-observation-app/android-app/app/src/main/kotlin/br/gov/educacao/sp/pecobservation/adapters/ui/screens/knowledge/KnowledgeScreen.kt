package br.gov.educacao.sp.pecobservation.adapters.ui.screens.knowledge

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import br.gov.educacao.sp.pecobservation.adapters.ui.viewmodels.KnowledgeViewModel
import br.gov.educacao.sp.pecobservation.domain.entities.FeedbackStyle
import br.gov.educacao.sp.pecobservation.domain.entities.KnowledgeDocument
import br.gov.educacao.sp.pecobservation.domain.entities.StyleTone

@Composable
fun KnowledgeScreen(vm: KnowledgeViewModel = hiltViewModel()) {
    val documents by vm.documents.collectAsStateWithLifecycle()
    val styles    by vm.styles.collectAsStateWithLifecycle()
    val isLoading by vm.isLoading.collectAsStateWithLifecycle()

    var selectedTab     by remember { mutableIntStateOf(0) }
    var showNewStyle    by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) { vm.loadAll() }

    Scaffold(
        topBar = { TopAppBar(title = { Text("Base de Conhecimento") }) },
        floatingActionButton = {
            if (selectedTab == 1) {
                FloatingActionButton(onClick = { showNewStyle = true }) {
                    Icon(Icons.Default.Add, "Novo estilo")
                }
            }
        },
    ) { padding ->
        Column(modifier = Modifier.padding(padding)) {
            TabRow(selectedTabIndex = selectedTab) {
                Tab(selected = selectedTab == 0, onClick = { selectedTab = 0 },
                    text = { Text("Documentos") })
                Tab(selected = selectedTab == 1, onClick = { selectedTab = 1 },
                    text = { Text("Estilos") })
            }

            if (isLoading) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            } else when (selectedTab) {
                0 -> DocumentsTab(documents, onDelete = { vm.deleteDocument(it) })
                1 -> StylesTab(styles, onDelete = { vm.deleteStyle(it) })
            }
        }
    }

    if (showNewStyle) {
        NewStyleDialog(
            onDismiss = { showNewStyle = false },
            onCreate  = { name, desc, tone, prompt, strengths, improvements, isDefault ->
                vm.createStyle(name, desc, tone.name.lowercase(), prompt, strengths, improvements, isDefault)
                showNewStyle = false
            },
        )
    }
}

@Composable
private fun DocumentsTab(
    documents: List<KnowledgeDocument>,
    onDelete: (String) -> Unit,
) {
    if (documents.isEmpty()) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Text("Nenhum documento.\nAdicione documentos da SEDUC para enriquecer o feedback da IA.",
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.padding(32.dp))
        }
    } else {
        LazyColumn {
            items(documents, key = { it.id }) { doc ->
                ListItem(
                    headlineContent  = { Text(doc.title) },
                    supportingContent = {
                        Column {
                            Text(doc.documentTypeDisplay, style = MaterialTheme.typography.labelSmall)
                            doc.description?.let { Text(it, maxLines = 2) }
                        }
                    },
                    trailingContent  = {
                        Column(horizontalAlignment = Alignment.End) {
                            Text("${doc.chunkCount} trechos", style = MaterialTheme.typography.labelSmall)
                            IconButton(onClick = { onDelete(doc.id) }) {
                                Icon(Icons.Default.Delete, "Excluir", tint = MaterialTheme.colorScheme.error)
                            }
                        }
                    },
                )
                HorizontalDivider()
            }
        }
    }
}

@Composable
private fun StylesTab(
    styles: List<FeedbackStyle>,
    onDelete: (String) -> Unit,
) {
    if (styles.isEmpty()) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Text("Nenhum estilo de feedback configurado.",
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.padding(32.dp))
        }
    } else {
        LazyColumn {
            items(styles, key = { it.id }) { style ->
                ListItem(
                    headlineContent  = {
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Text(style.name)
                            if (style.isDefault) {
                                SuggestionChip(onClick = {}, label = { Text("Padrão") })
                            }
                        }
                    },
                    supportingContent = {
                        Column {
                            Text("Tom: ${style.toneDisplay}", style = MaterialTheme.typography.labelSmall)
                            Text(style.description, maxLines = 2)
                        }
                    },
                    trailingContent = {
                        IconButton(onClick = { onDelete(style.id) }) {
                            Icon(Icons.Default.Delete, "Excluir", tint = MaterialTheme.colorScheme.error)
                        }
                    },
                )
                HorizontalDivider()
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun NewStyleDialog(
    onDismiss: () -> Unit,
    onCreate: (String, String, StyleTone, String, List<String>, List<String>, Boolean) -> Unit,
) {
    var name        by remember { mutableStateOf("") }
    var desc        by remember { mutableStateOf("") }
    var tone        by remember { mutableStateOf(StyleTone.CONSTRUCTIVE) }
    var prompt      by remember { mutableStateOf("") }
    var strengths   by remember { mutableStateOf("") }
    var improvements by remember { mutableStateOf("") }
    var isDefault   by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title   = { Text("Novo Estilo de Feedback") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp),
                   modifier = Modifier.fillMaxWidth()) {
                OutlinedTextField(value = name, onValueChange = { name = it },
                    label = { Text("Nome") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = desc, onValueChange = { desc = it },
                    label = { Text("Descrição") }, modifier = Modifier.fillMaxWidth())
                ExposedDropdownMenuBox(expanded = false, onExpandedChange = {}) {
                    OutlinedTextField(value = tone.displayName, onValueChange = {},
                        label = { Text("Tom") }, readOnly = true,
                        modifier = Modifier.fillMaxWidth().menuAnchor())
                }
                OutlinedTextField(value = prompt, onValueChange = { prompt = it },
                    label = { Text("Instrução para a IA") },
                    modifier = Modifier.fillMaxWidth(), minLines = 3)
                OutlinedTextField(value = strengths, onValueChange = { strengths = it },
                    label = { Text("Exemplos de forças (uma por linha)") },
                    modifier = Modifier.fillMaxWidth(), minLines = 2)
                OutlinedTextField(value = improvements, onValueChange = { improvements = it },
                    label = { Text("Exemplos de melhorias (uma por linha)") },
                    modifier = Modifier.fillMaxWidth(), minLines = 2)
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(checked = isDefault, onCheckedChange = { isDefault = it })
                    Text("Definir como padrão")
                }
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    val s = strengths.lines().filter { it.isNotBlank() }
                    val i = improvements.lines().filter { it.isNotBlank() }
                    onCreate(name, desc, tone, prompt, s, i, isDefault)
                },
                enabled = name.isNotBlank() && prompt.isNotBlank(),
            ) { Text("Criar") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancelar") } },
    )
}
