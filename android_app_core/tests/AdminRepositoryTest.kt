package com.hospital.urgencias.data.repository

import com.hospital.urgencias.di.HospitalApiService
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.runBlocking
import org.junit.Test
import kotlin.test.assertTrue

class AdminRepositoryTest {

    private val apiService = mockk<HospitalApiService>()
    private val repository = AdminRepositoryImpl(apiService)

    @Test
    fun `fetchAIInsights deve mapear corretamente os dados do backend`() = runBlocking {
        // Simulando resposta do FastAPI/analytics_afluencia.py
        coEvery { apiService.getAIInsights() } returns AIInsightResponse(
            inflow = 20,
            prediction = 25,
            risk = 0.85,
            tips = listOf("Alerta de Saturação")
        )

        val result = repository.getAIInsights().first()

        // Validando se o risco crítico é detetado
        assertTrue(result.saturationRisk > 0.8)
        assertTrue(result.recommendations.contains("Alerta de Saturação"))
    }
}
