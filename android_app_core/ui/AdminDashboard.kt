package com.hospital.urgencias.ui.admin

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*

@Composable
fun AdminDashboardScreen(viewModel: AdminUniversalViewModel) {
    val state = viewModel.uiState.collectAsState().value

    Scaffold(
        topBar = { TopAppBar(title = { Text("Painel Universal Admin") }) }
    ) { padding ->
        Column(modifier = Modifier.padding(padding).fillMaxSize()) {
            
            // Secção de IA (Destaque)
            state.aiInsight?.let { ai ->
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = if(ai.saturationRisk > 0.7) MaterialTheme.colorScheme.errorContainer 
                                         else MaterialTheme.colorScheme.primaryContainer
                    ),
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp)
                        .testTag("ai_insight_card") // Tag para o teste
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("Insight da IA", style = MaterialTheme.typography.titleLarge)
                        Text("Previsão de Afluência: ${ai.predictedInflowNextHour} pacientes/hora", modifier = Modifier.testTag("ai_prediction_text"))
                        Text("Risco de Saturação: ${(ai.saturationRisk * 100).toInt()}%")
                        ai.recommendations.forEach { Text("• $it") }
                    }
                }
            }

            // Lista de Utilizadores (Acesso Universal)
            Text("Gestão de Profissionais", style = MaterialTheme.typography.headlineSmall, modifier = Modifier.padding(16.dp))
            LazyColumn {
                items(state.users) { user ->
                    UserListItem(user, onToggle = { viewModel.toggleUserStatus(user.id, !user.isActive) })
                }
            }
        }
    }
}
