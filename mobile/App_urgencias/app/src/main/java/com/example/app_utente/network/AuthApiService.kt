package com.example.app_utente.network

import com.example.app_utente.model.*
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

interface AuthApiService {
    @POST("clinical/utentes/login")
    suspend fun login(@Body request: LoginRequest): Response<ApiResponse<LoginResponse>>

    @POST("clinical/utentes")
    suspend fun register(@Body request: RegisterRequest): Response<ApiResponse<Utente>>

    @POST("auth/login/mfa")
    suspend fun verifyMfa(@Body request: MfaRequest): Response<ApiResponse<LoginResponse>>

    @POST("auth/forgot-password")
    suspend fun recoverAccess(@Body numUtente: String): Response<ApiResponse<String>>

    @retrofit2.http.GET("clinical/utentes/{numUtente}/history")
    suspend fun getHistory(@retrofit2.http.Path("numUtente") numUtente: String): Response<ApiResponse<List<UrgenciaHistory>>>
}
