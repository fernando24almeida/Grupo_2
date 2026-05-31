package com.hospital.urgencias.ui.admin

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.hospital.urgencias.domain.model.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class AdminUniversalViewModel @Inject constructor(
    private val repository: AdminRepository
) : ViewModel() {

    // Estado unificado do Dashboard do Administrador
    private val _uiState = MutableStateFlow(AdminUiState())
    val uiState: StateFlow<AdminUiState> = _uiState.asStateFlow()

    init {
        loadAllData()
    }

    fun loadAllData() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            
            // Carregamento paralelo de dados universais e IA
            combine(
                repository.getUsers(),
                repository.getAIInsights(),
                repository.getAuditLogs()
            ) { users, ai, logs ->
                AdminUiState(
                    users = users,
                    aiInsight = ai,
                    auditLogs = logs,
                    isLoading = false
                )
            }.collect { newState ->
                _uiState.value = newState
            }
        }
    }

    fun toggleUserStatus(userId: Int, isActive: Boolean) {
        viewModelScope.launch {
            repository.updateUserStatus(userId, isActive)
            loadAllData() // Atualiza a vista após alteração
        }
    }
}

data class AdminUiState(
    val users: List<User> = emptyList(),
    val aiInsight: AIInsight? = null,
    val auditLogs: List<AuditLog> = emptyList(),
    val isLoading: Boolean = false
)
