package com.example.app_utente.model

import com.google.gson.annotations.SerializedName

data class Utente(
    @SerializedName("num_utente") val numUtente: String,
    @SerializedName("nome") val nome: String,
    @SerializedName("email") val email: String? = null
)

data class LoginRequest(
    @SerializedName("num_utente") val numUtente: String,
    @SerializedName("pin") val pin: String
)

data class LoginResponse(
    @SerializedName("token") val token: String,
    @SerializedName("mfa_required") val mfaRequired: Boolean,
    @SerializedName("utente") val utente: Utente? = null
)

data class RegisterRequest(
    @SerializedName("num_utente") val numUtente: String,
    @SerializedName("nome") val nome: String,
    @SerializedName("pin") val pin: String,
    @SerializedName("email") val email: String
)

data class MfaRequest(
    @SerializedName("num_utente") val numUtente: String,
    @SerializedName("code") val code: String
)

data class ApiResponse<T>(
    @SerializedName("success") val success: Boolean,
    @SerializedName("message") val message: String?,
    @SerializedName("data") val data: T?
)

data class UrgenciaHistory(
    @SerializedName("id") val id: String,
    @SerializedName("data") val data: String,
    @SerializedName("hospital") val hospital: String,
    @SerializedName("estado") val estado: String,
    @SerializedName("prioridade") val prioridade: String // Cor da pulseira
)
