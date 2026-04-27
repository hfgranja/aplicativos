package br.gov.educacao.sp.pecobservation.adapters.ui.screens

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CloudSync
import androidx.compose.material.icons.filled.List
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.School
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import br.gov.educacao.sp.pecobservation.adapters.ui.screens.knowledge.KnowledgeScreen
import br.gov.educacao.sp.pecobservation.adapters.ui.screens.observations.ObservationListScreen
import br.gov.educacao.sp.pecobservation.adapters.ui.screens.schools.SchoolListScreen
import br.gov.educacao.sp.pecobservation.adapters.ui.screens.sync.SyncStatusScreen

private sealed class NavRoute(val route: String, val label: String) {
    object Observations : NavRoute("observations", "Observações")
    object Schools      : NavRoute("schools",      "Escolas")
    object Knowledge    : NavRoute("knowledge",    "Conhecimento")
    object Sync         : NavRoute("sync",         "Sincronização")
}

@Composable
fun MainScreen() {
    val navController = rememberNavController()
    val tabs = listOf(NavRoute.Observations, NavRoute.Schools, NavRoute.Knowledge, NavRoute.Sync)

    Scaffold(
        bottomBar = {
            NavigationBar {
                val backStack by navController.currentBackStackEntryAsState()
                val current = backStack?.destination
                tabs.forEach { tab ->
                    NavigationBarItem(
                        selected = current?.hierarchy?.any { it.route == tab.route } == true,
                        onClick  = {
                            navController.navigate(tab.route) {
                                popUpTo(navController.graph.findStartDestination().id) { saveState = true }
                                launchSingleTop = true
                                restoreState    = true
                            }
                        },
                        icon = {
                            Icon(
                                imageVector = when (tab) {
                                    NavRoute.Observations -> Icons.Default.List
                                    NavRoute.Schools      -> Icons.Default.School
                                    NavRoute.Knowledge    -> Icons.Default.MenuBook
                                    NavRoute.Sync         -> Icons.Default.CloudSync
                                },
                                contentDescription = tab.label,
                            )
                        },
                        label = { Text(tab.label) },
                    )
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController    = navController,
            startDestination = NavRoute.Observations.route,
            modifier         = Modifier.padding(innerPadding),
        ) {
            composable(NavRoute.Observations.route) { ObservationListScreen(navController) }
            composable(NavRoute.Schools.route)      { SchoolListScreen() }
            composable(NavRoute.Knowledge.route)    { KnowledgeScreen() }
            composable(NavRoute.Sync.route)         { SyncStatusScreen() }
        }
    }
}
