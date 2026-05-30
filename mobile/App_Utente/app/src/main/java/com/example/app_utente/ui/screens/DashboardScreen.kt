package com.example.app_utente.ui.screens

import android.util.Log
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.KeyboardArrowRight
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.app_utente.model.UrgenciaHistory
import com.example.app_utente.network.NetworkModule
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(
    numUtente: String,
    onLogout: () -> Unit,
    onEpisodeClick: (String) -> Unit
) {
    var history by remember { mutableStateOf<List<UrgenciaHistory>>(emptyList()) }
    var isLoading by remember { mutableStateOf(true) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()
    val context = androidx.compose.ui.platform.LocalContext.current
    val userName = remember { com.example.app_utente.security.SecurityUtils.getUserName(context) ?: "" }

    LaunchedEffect(numUtente) {
        scope.launch {
            Log.d("DashboardScreen", "Fetching episodes (automatic filter by token)")
            try {
                val response = NetworkModule.apiService.getEpisodes()
                if (response.isSuccessful) {
                    val data = response.body()
                    Log.d("DashboardScreen", "Episodes fetch successful. Items: ${data?.size ?: 0}")
                    history = data ?: emptyList()
                } else {
                    val errorBody = response.errorBody()?.string()
                    Log.e("DashboardScreen", "Error response: ${response.code()} $errorBody")
                    errorMessage = "Erro ao carregar histórico: ${response.code()}"
                }
            } catch (e: Exception) {
                Log.e("DashboardScreen", "Connection exception: ${e.localizedMessage}", e)
                errorMessage = "Erro de conexão com o servidor"
            } finally {
                isLoading = false
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { 
                    Column {
                        Text("Urgências G2", style = MaterialTheme.typography.titleLarge)
                        Text("Portal do Utente", style = MaterialTheme.typography.labelMedium)
                    }
                },
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
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                )
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = if (userName.isNotEmpty()) userName else "Bem-vindo,",
                            style = MaterialTheme.typography.headlineSmall,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                        Text(
                            text = "Utente $numUtente",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                    }
                }
            }
            
            Spacer(modifier = Modifier.height(24.dp))

            Text(
                text = "Histórico de Episódios", 
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(16.dp))

            if (isLoading) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            } else if (errorMessage != null) {
                Column(
                    modifier = Modifier.fillMaxSize(),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    Text(text = errorMessage!!, color = MaterialTheme.colorScheme.error)
                    Button(onClick = { /* Retry logic could go here */ }, modifier = Modifier.padding(top = 8.dp)) {
                        Text("Tentar Novamente")
                    }
                }
            } else if (history.isEmpty()) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text(text = "Nenhum histórico encontrado.", style = MaterialTheme.typography.bodyLarge)
                }
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                    contentPadding = PaddingValues(bottom = 16.dp)
                ) {
                    items(history) { item ->
                        HistoryCard(item, onClick = { item.id?.let { onEpisodeClick(it) } })
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HistoryCard(item: UrgenciaHistory, onClick: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        onClick = onClick,
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        )
    ) {
        Row(
            modifier = Modifier
                .padding(16.dp)
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            PriorityIndicator(item.prioridade ?: "Verde")
            Spacer(modifier = Modifier.width(16.dp))
            Column(modifier = Modifier.weight(1f)) {
                val displayDate = item.data?.replace("T", " ")?.take(16) ?: "Data N/A"
                Text(
                    text = displayDate,
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(
                    text = item.hospital ?: "Hospital N/A",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = item.estado ?: "Estado N/A",
                    style = MaterialTheme.typography.bodyMedium,
                    maxLines = 1,
                    overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis
                )
                Text(
                    text = "Ver detalhes",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Medium
                )
            }
            Icon(
                imageVector = androidx.compose.material.icons.Icons.Default.KeyboardArrowRight,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary
            )
        }
    }
}

@Composable
fun PriorityIndicator(prioridade: String) {
    val color = when (prioridade.lowercase()) {
        "vermelho" -> Color.Red
        "laranja" -> Color(0xFFFFA500)
        "amarelo" -> Color(0xFFFBC02D)
        "verde" -> Color(0xFF4CAF50)
        "azul" -> Color.Blue
        else -> Color.Gray
    }
    
    Box(
        modifier = Modifier
            .size(width = 4.dp, height = 40.dp)
            .background(color = color, shape = MaterialTheme.shapes.small)
    )
}

