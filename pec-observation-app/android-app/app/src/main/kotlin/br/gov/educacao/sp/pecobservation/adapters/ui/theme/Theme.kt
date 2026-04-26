package br.gov.educacao.sp.pecobservation.adapters.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import android.os.Build

private val LightColors = lightColorScheme(
    primary          = Color(0xFF004BA0),
    onPrimary        = Color.White,
    primaryContainer = Color(0xFFD6E4FF),
    secondary        = Color(0xFF005B4F),
    onSecondary      = Color.White,
    error            = Color(0xFFB00020),
    background       = Color(0xFFFAFAFA),
    surface          = Color.White,
)

private val DarkColors = darkColorScheme(
    primary          = Color(0xFF9ECAFF),
    onPrimary        = Color(0xFF003258),
    primaryContainer = Color(0xFF004880),
    secondary        = Color(0xFF4CDBC4),
    onSecondary      = Color(0xFF003730),
    background       = Color(0xFF1A1C1E),
    surface          = Color(0xFF1A1C1E),
)

@Composable
fun PECObservationTheme(
    darkTheme: Boolean = androidx.compose.foundation.isSystemInDarkTheme(),
    dynamicColor: Boolean = Build.VERSION.SDK_INT >= Build.VERSION_CODES.S,
    content: @Composable () -> Unit,
) {
    val colorScheme = when {
        dynamicColor && darkTheme  -> dynamicDarkColorScheme(LocalContext.current)
        dynamicColor && !darkTheme -> dynamicLightColorScheme(LocalContext.current)
        darkTheme                  -> DarkColors
        else                       -> LightColors
    }
    MaterialTheme(colorScheme = colorScheme, typography = Typography, content = content)
}
