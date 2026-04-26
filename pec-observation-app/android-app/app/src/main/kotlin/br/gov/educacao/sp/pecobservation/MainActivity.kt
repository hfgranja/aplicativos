package br.gov.educacao.sp.pecobservation

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import br.gov.educacao.sp.pecobservation.adapters.ui.screens.MainScreen
import br.gov.educacao.sp.pecobservation.adapters.ui.theme.PECObservationTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            PECObservationTheme {
                MainScreen()
            }
        }
    }
}
