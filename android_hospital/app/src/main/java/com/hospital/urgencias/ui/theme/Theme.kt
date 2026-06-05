package com.hospital.urgencias.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.*
import androidx.compose.runtime.Composable

private val LightColorScheme = lightColorScheme(
    primary = HospitalBlue,
    secondary = HospitalGreen,
    background = BackgroundGray,
    surface = SurfaceWhite,
    error = AlertRed
)

@Composable
fun HospitalTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = LightColorScheme, // Foco em interface Clara para ambientes hospitalares
        content = content
    )
}
