package com.hospital.urgencias.di

import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object HospitalModule {

    @Provides
    @Singleton
    fun provideRetrofit(): Retrofit = Retrofit.Builder()
        .baseUrl("http://10.0.2.2:8000/api/") // Endereço para o FastAPI no localhost
        .addConverterFactory(GsonConverterFactory.create())
        .build()

    @Provides
    @Singleton
    fun provideApiService(retrofit: Retrofit): HospitalApiService = 
        retrofit.create(HospitalApiService::class.java)
}

// Interface que espelha os seus endpoints FastAPI
interface HospitalApiService {
    @GET("admin/users")
    suspend fun getUsers(): List<UserResponse>

    @GET("analytics/ai-insights")
    suspend fun getAIInsights(): AIInsightResponse

    @GET("admin/audit-logs")
    suspend fun getAuditLogs(): List<AuditLogResponse>
}
