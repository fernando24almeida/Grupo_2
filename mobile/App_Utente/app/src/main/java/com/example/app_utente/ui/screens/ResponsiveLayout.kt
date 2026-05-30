package com.example.app_utente.ui.screens

import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.runtime.Composable

@Composable
fun ResponsiveLayout(
    content: @Composable (isPortrait: Boolean) -> Unit
) {
    BoxWithConstraints {
        val isPortrait = maxHeight > maxWidth
        content(isPortrait)
    }
}
