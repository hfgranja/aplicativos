package br.gov.educacao.sp.pecobservation.adapters.ui.screens.schools

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import br.gov.educacao.sp.pecobservation.adapters.ui.viewmodels.SchoolListViewModel
import br.gov.educacao.sp.pecobservation.domain.entities.School

@Composable
fun SchoolListScreen(vm: SchoolListViewModel = hiltViewModel()) {
    val schools by vm.schools.collectAsStateWithLifecycle()
    var showAdd by remember { mutableStateOf(false) }

    Scaffold(
        topBar = { TopAppBar(title = { Text("Escolas") }) },
        floatingActionButton = {
            FloatingActionButton(onClick = { showAdd = true }) {
                Icon(Icons.Default.Add, contentDescription = "Adicionar escola")
            }
        },
    ) { padding ->
        if (schools.isEmpty()) {
            Box(Modifier.fillMaxSize().padding(padding), contentAlignment = Alignment.Center) {
                Text("Nenhuma escola cadastrada", style = MaterialTheme.typography.bodyLarge)
            }
        } else {
            LazyColumn(contentPadding = padding) {
                items(schools, key = { it.id.toString() }) { school ->
                    ListItem(
                        headlineContent  = { Text(school.name) },
                        supportingContent = { Text("INEP: ${school.inepCode}") },
                    )
                    HorizontalDivider()
                }
            }
        }
    }

    if (showAdd) {
        AddSchoolDialog(
            onDismiss = { showAdd = false },
            onAdd     = { name, inep -> vm.addSchool(name, inep); showAdd = false },
        )
    }
}

@Composable
private fun AddSchoolDialog(onDismiss: () -> Unit, onAdd: (String, String) -> Unit) {
    var name by remember { mutableStateOf("") }
    var inep by remember { mutableStateOf("") }
    AlertDialog(
        onDismissRequest = onDismiss,
        title   = { Text("Nova Escola") },
        text    = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(value = name, onValueChange = { name = it }, label = { Text("Nome") })
                OutlinedTextField(value = inep, onValueChange = { inep = it }, label = { Text("Código INEP") })
            }
        },
        confirmButton = {
            TextButton(onClick = { onAdd(name, inep) }, enabled = name.isNotBlank() && inep.isNotBlank()) {
                Text("Adicionar")
            }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancelar") } },
    )
}
