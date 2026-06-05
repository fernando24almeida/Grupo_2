package com.hospital.urgencias.domain.model

import kotlinx.coroutines.flow.Flow

interface AdminRepository {
    fun getUsers(): Flow<List<User>>
    fun getAIInsights(): Flow<AIInsight>
    fun getAuditLogs(): Flow<List<AuditLog>>
    suspend fun updateUserStatus(userId: Int, isActive: Boolean)
}
