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

data class RecoverRequest(
    @SerializedName("num_utente") val numUtente: String
)

data class ApiResponse<T>(
    @SerializedName("success") val success: Boolean,
    @SerializedName("message") val message: String?,
    @SerializedName("data") val data: T?
)

data class ProfissionalInfo(
    @SerializedName("nome") val nome: String?,
    @SerializedName("num_func") val numFunc: Any?
)

data class TriagemInfo(
    @SerializedName("prioridade") val prioridade: String?,
    @SerializedName("temperatura") val temperatura: Double?,
    @SerializedName("tensao_arterial") val tensaoArterial: String?,
    @SerializedName("sintomas") val sintomas: String?,
    @SerializedName("observacoes") val observacoes: String?,
    @SerializedName("profissional_info") val profissional: ProfissionalInfo?
)

data class TratamentoInfo(
    @SerializedName("descricao") val descricao: String?,
    @SerializedName("data_h_tratamento") val data: String?
)

data class ConsultaInfo(
    @SerializedName("notas") val notas: String?,
    @SerializedName("diagnostico") val diagnostico: String?,
    @SerializedName("profissional_info") val profissional: ProfissionalInfo?
)

data class UrgenciaHistory(
    @SerializedName("cod_epis") val id: String?,
    @SerializedName("data_h_entrada") val data: String?,
    @SerializedName("id_hospital") val hospital: String?,
    @SerializedName("sintomas_iniciais") val estado: String?,
    
    @SerializedName("triagem") val triagem: TriagemInfo? = null,
    @SerializedName("consulta") val consulta: ConsultaInfo? = null,
    @SerializedName("tratamentos") val tratamentos: List<TratamentoInfo>? = null,
    @SerializedName("internamentos") val internamentos: String? = null,
    @SerializedName("medico_responsavel") val medico: String? = null,
    
    // Suporte para campo prioridade vindo direto ou da triagem
    @SerializedName("prioridade") private val _prioridade: String? = null
) {
    val prioridade: String?
        get() = _prioridade ?: triagem?.prioridade
}
