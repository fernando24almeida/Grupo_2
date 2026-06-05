package com.hospital.urgencias.ui.admin

import io.mockk.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.*
import org.junit.After
import org.junit.Before
import org.junit.Test
import kotlin.test.assertEquals

@OptIn(ExperimentalCoroutinesApi::class)
class AdminUniversalViewModelTest {

    private val repository = mockk<AdminRepository>()
    private lateinit var viewModel: AdminUniversalViewModel
    private val testDispatcher = UnconfinedTestDispatcher()

    @Before
    fun setup() {
        Dispatchers.setMain(testDispatcher)
        
        // Mock dos dados de IA e Utilizadores
        coEvery { repository.getUsers() } returns flowOf(listOf(User(1, "Dr. House", "MEDICO", true)))
        coEvery { repository.getAIInsights() } returns flowOf(AIInsight(10, 15, 0.4, listOf("Reforço necessário")))
        coEvery { repository.getAuditLogs() } returns flowOf(emptyList())
        
        viewModel = AdminUniversalViewModel(repository)
    }

    @Test
    fun `loadAllData deve atualizar o estado da UI com dados do repositório`() = runTest {
        val state = viewModel.uiState.value
        
        // Verificar se a IA foi carregada corretamente
        assertEquals(15, state.aiInsight?.predictedInflowNextHour)
        assertEquals("Dr. House", state.users.first().username)
        assertEquals(false, state.isLoading)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }
}
