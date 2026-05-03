package com.example.app_utente.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.example.app_utente.model.UrgenciaHistory
import com.example.app_utente.network.NetworkModule
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(
    numUtente: String,
    onLogout: () -> Unit
) {
    var history by remember { mutableStateOf<List<UrgenciaHistory>>(emptyList()) }
    var isLoading by remember { mutableStateOf(true) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    LaunchedEffect(numUtente) {
        scope.launch {
            try {
                val response = NetworkModule.apiService.getHistory(numUtente)
                if (response.isSuccessful) {
                    history = response.body()?.data ?: emptyList()
                } else {
                    errorMessage = "Erro ao carregar histórico"
                }
            } catch (e: Exception) {
                errorMessage = "Erro de conexão"
            } finally {
                isLoading = false
            }
        }
    }

    ResponsiveLayout { isPortrait ->
        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text("Urgências G2 - Utente") },
                    actions = {
                        TextButton(onClick = onLogout) {
                            Text("Sair", color = MaterialTheme.colorScheme.error)
                        }
                    }
                )
            }
        ) { padding ->
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(16.dp)
            ) {
                Text(
                    text = "Nº Utente: $numUtente",
                    style = MaterialTheme.typography.headlineMedium
                )
                Spacer(modifier = Modifier.height(24.dp))

                Text(text = "Histórico de Atendimentos", style = MaterialTheme.typography.titleLarge)
                Spacer(modifier = Modifier.height(16.dp))

                if (isLoading) {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        CircularProgressIndicator()
                    }
                } else if (errorMessage != null) {
                    Text(text = errorMessage!!, color = MaterialTheme.colorScheme.error)
                } else if (history.isEmpty()) {
                    Text(text = "Nenhum histórico encontrado.")
                } else {
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        items(history) { item ->
                            HistoryCard(item)
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun HistoryCard(item: UrgenciaHistory) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(text = item.data, style = MaterialTheme.typography.labelMedium)
                PriorityBadge(item.prioridade)
            }
            Spacer(modifier = Modifier.height(4.dp))
            Text(text = item.hospital, style = MaterialTheme.typography.titleMedium)
            Text(text = "Estado: ${item.estado}", style = MaterialTheme.typography.bodyMedium)
        }
    }
}

@Composable
fun PriorityBadge(prioridade: String) {
    val color = when (prioridade.lowercase()) {
        "vermelho" -> Color.Red
        "laranja" -> Color(0xFFFFA500)
        "amarelo" -> Color.Yellow
        "verde" -> Color.Green
        "azul" -> Color.Blue
        else -> Color.Gray
    }
    
    Surface(
        color = color,
        shape = MaterialTheme.shapes.small,
        modifier = Modifier.size(width = 60.dp, height = 20.dp)
    ) {
        // Just a color badge
    }
}
