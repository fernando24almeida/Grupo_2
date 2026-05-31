package com.hospital.urgencias.data.repository

import com.hospital.urgencias.di.HospitalApiService
import com.hospital.urgencias.domain.model.*
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import javax.inject.Inject

class AdminRepositoryImpl @Inject constructor(
    private val api: HospitalApiService
) : AdminRepository {

    override fun getUsers(): Flow<List<User>> = flow {
        val response = api.getUsers()
        emit(response.map { it.toDomain() })
    }

    override fun getAIInsights(): Flow<AIInsight> = flow {
        val response = api.getAIInsights()
        emit(response.toDomain())
    }

    override fun getAuditLogs(): Flow<List<AuditLog>> = flow {
        val response = api.getAuditLogs()
        emit(response.map { it.toDomain() })
    }

    override suspend fun updateUserStatus(userId: Int, isActive: Boolean) {
        api.updateStatus(userId, StatusRequest(isActive))
    }
}
