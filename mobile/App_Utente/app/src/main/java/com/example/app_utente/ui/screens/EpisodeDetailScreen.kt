package com.example.app_utente.ui.screens

import android.util.Log
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.app_utente.model.UrgenciaHistory
import com.example.app_utente.network.NetworkModule
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EpisodeDetailScreen(
    episodeId: String,
    onNavigateBack: () -> Unit
) {
    var episode by remember { mutableStateOf<UrgenciaHistory?>(null) }
    var isLoading by remember { mutableStateOf(true) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    LaunchedEffect(episodeId) {
        Log.d("EpisodeDetailScreen", "Iniciando busca do episódio: $episodeId")
        scope.launch {
            try {
                val response = NetworkModule.apiService.getEpisodeDetails(episodeId)
                if (response.isSuccessful) {
                    episode = response.body()
                    Log.d("EpisodeDetailScreen", "Detalhes carregados com sucesso")
                } else {
                    Log.e("EpisodeDetailScreen", "Erro API: ${response.code()} - ${response.errorBody()?.string()}")
                    errorMessage = "Erro no servidor: ${response.code()}"
                }
            } catch (e: Exception) {
                Log.e("EpisodeDetailScreen", "Exceção ao buscar detalhes: ${e.message}", e)
                errorMessage = "Erro de ligação: ${e.localizedMessage ?: "Verifique a internet"}"
            } finally {
                isLoading = false
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Detalhes do Episódio") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Voltar")
                    }
                }
            )
        }
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            if (isLoading) {
                CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
            } else if (errorMessage != null) {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    Text(text = errorMessage!!, color = MaterialTheme.colorScheme.error)
                    Button(onClick = onNavigateBack, modifier = Modifier.padding(top = 16.dp)) {
                        Text("Voltar")
                    }
                }
            } else if (episode != null) {
                EpisodeDetailContent(episode!!)
            }
        }
    }
}

@Composable
fun EpisodeDetailContent(episode: UrgenciaHistory) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp)
    ) {
        DetailHeader(episode)
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Informações Gerais
        DetailSection(
            title = "Informações Gerais",
            icon = Icons.Default.Info
        ) {
            DetailItem(label = "Referência", value = episode.id)
            val displayDate = episode.data?.replace("T", " ")?.take(16) ?: "N/A"
            DetailItem(label = "Data de Entrada", value = displayDate)
            DetailItem(label = "Hospital", value = episode.hospital)
            if (episode.medico != null) {
                DetailItem(label = "Médico Responsável", value = episode.medico)
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Triagem
        val triagem = episode.triagem
        if (triagem != null) {
            DetailSection(
                title = "Triagem",
                icon = Icons.Default.Notifications
            ) {
                DetailItem(label = "Prioridade", value = triagem.prioridade ?: "N/A")
                DetailItem(label = "Sintomas na triagem", value = triagem.sintomas)
                
                Row(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.weight(1f)) {
                        DetailItem(label = "Temperatura", value = triagem.temperatura?.let { "$it ºC" })
                    }
                    Column(modifier = Modifier.weight(1f)) {
                        DetailItem(label = "Tensão Arterial", value = triagem.tensaoArterial)
                    }
                }
                
                if (triagem.observacoes != null) {
                    DetailItem(label = "Observações", value = triagem.observacoes)
                }
                
                if (triagem.profissional?.nome != null) {
                    DetailItem(label = "Enfermeiro(a)", value = triagem.profissional.nome)
                }
            }
            Spacer(modifier = Modifier.height(24.dp))
        }

        // Consulta / Diagnóstico
        val consulta = episode.consulta
        if (consulta != null || episode.estado != null) {
            DetailSection(
                title = "Consulta e Diagnóstico",
                icon = Icons.Default.Edit
            ) {
                DetailItem(label = "Sintomas iniciais (reportados)", value = episode.estado)
                
                if (consulta != null) {
                    if (consulta.notas != null) {
                        DetailItem(label = "Notas da Consulta", value = consulta.notas)
                    }
                    if (consulta.diagnostico != null) {
                        DetailItem(label = "Diagnóstico Final", value = consulta.diagnostico)
                    }
                    if (consulta.profissional?.nome != null) {
                        DetailItem(label = "Médico(a)", value = consulta.profissional.nome)
                    }
                }
            }
            Spacer(modifier = Modifier.height(24.dp))
        }

        // Tratamentos
        if (!episode.tratamentos.isNullOrEmpty()) {
            DetailSection(
                title = "Tratamentos e Procedimentos",
                icon = Icons.Default.Build
            ) {
                episode.tratamentos.forEach { tratamento ->
                    Column(modifier = Modifier.padding(vertical = 4.dp)) {
                        Text(
                            text = "• ${tratamento.descricao ?: "Tratamento"}",
                            style = MaterialTheme.typography.bodyLarge,
                            fontWeight = FontWeight.Medium
                        )
                        if (tratamento.data != null) {
                            Text(
                                text = tratamento.data.replace("T", " ").take(16),
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }
            }
            Spacer(modifier = Modifier.height(24.dp))
        }

        // Internamentos
        if (episode.internamentos != null) {
            DetailSection(
                title = "Internamentos",
                icon = Icons.Default.Home
            ) {
                DetailItem(label = "Detalhes do Internamento", value = episode.internamentos)
            }
            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}

@Composable
fun DetailHeader(episode: UrgenciaHistory) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = getPriorityColor(episode.prioridade ?: "Verde").copy(alpha = 0.1f)
        )
    ) {
        Row(
            modifier = Modifier
                .padding(16.dp)
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(12.dp)
                    .background(
                        color = getPriorityColor(episode.prioridade ?: "Verde"),
                        shape = MaterialTheme.shapes.small
                    )
            )
            Spacer(modifier = Modifier.width(12.dp))
            Column {
                Text(
                    text = "Prioridade ${episode.prioridade ?: "Verde"}",
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                    color = getPriorityColor(episode.prioridade ?: "Verde")
                )
                Text(
                    text = episode.hospital ?: "Hospital não especificado",
                    style = MaterialTheme.typography.bodyMedium
                )
            }
        }
    }
}

@Composable
fun DetailSection(
    title: String,
    icon: ImageVector,
    content: @Composable () -> Unit
) {
    Column {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary,
                modifier = Modifier.size(20.dp)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = title,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.primary
            )
        }
        HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))
        content()
    }
}

@Composable
fun DetailItem(label: String, value: String?) {
    Column(modifier = Modifier.padding(vertical = 4.dp)) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Text(
            text = value ?: "Não disponível",
            style = MaterialTheme.typography.bodyLarge,
            fontWeight = FontWeight.Medium
        )
    }
}

@Composable
fun getPriorityColor(prioridade: String): Color {
    return when (prioridade.lowercase()) {
        "vermelho" -> Color.Red
        "laranja" -> Color(0xFFFFA500)
        "amarelo" -> Color(0xFFFBC02D)
        "verde" -> Color(0xFF4CAF50)
        "azul" -> Color.Blue
        else -> Color.Gray
    }
}
