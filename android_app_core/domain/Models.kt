package com.hospital.urgencias.domain.model

data class User(
    val id: Int,
    val username: String,
    val role: String, // ADMIN, MEDICO, ENFERMEIRO
    val isActive: Boolean
)

data class AIInsight(
    val currentInflow: Int,
    val predictedInflowNextHour: Int,
    val saturationRisk: Double, // 0.0 a 1.0
    val recommendations: List<String>
)

data class AuditLog(
    val id: String,
    val action: String,
    val username: String,
    val timestamp: Long,
    val severity: String // INFO, WARNING, CRITICAL
)
