package com.hospital.urgencias.ui.admin

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.onNodeWithText
import org.junit.Rule
import org.junit.Test

class AdminDashboardUiTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun dashboard_quandoRiscoIAAlto_deveMostrarAlerta() {
        // 1. Criar um estado de UI simulado com risco de 85% (Crítico)
        val highRiskState = AdminUiState(
            aiInsight = AIInsight(
                currentInflow = 20,
                predictedInflowNextHour = 30,
                saturationRisk = 0.85,
                recommendations = listOf("Ativar Plano de Contingência")
            ),
            isLoading = false
        )

        // 2. Carregar o ecrã com este estado
        composeTestRule.setContent {
            // Aqui simulamos apenas a UI passando o estado diretamente ou via ViewModel mockada
            AdminDashboardContent(state = highRiskState) 
        }

        // 3. Verificar se o cartão de IA está visível
        composeTestRule.onNodeWithTag("ai_insight_card").assertIsDisplayed()

        // 4. Verificar se o texto de previsão correto está lá
        composeTestRule.onNodeWithText("Previsão de Afluência: 30 pacientes/hora").assertIsDisplayed()
        
        // 5. Verificar se a recomendação da IA aparece para o Admin
        composeTestRule.onNodeWithText("• Ativar Plano de Contingência").assertIsDisplayed()
    }
}
