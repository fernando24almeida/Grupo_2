package com.example.app_utente.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.app_utente.network.NetworkModule
import kotlinx.coroutines.launch

import com.example.app_utente.model.MfaRequest

@Composable
fun MfaScreen(
    numUtente: String,
    onMfaSuccess: () -> Unit,
    onNavigateBack: () -> Unit,
    onNavigateToRecover: () -> Unit
) {
    var code by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf<String?>(null) }
    var isError by remember { mutableStateOf(false) }

    val scope = rememberCoroutineScope()
    val apiService = NetworkModule.apiService

    ResponsiveLayout { isPortrait ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(text = "Autenticação MFA", style = MaterialTheme.typography.headlineLarge)
            Spacer(modifier = Modifier.height(16.dp))
            Text(text = "Insira o código enviado para o seu dispositivo.")
            Spacer(modifier = Modifier.height(32.dp))

            OutlinedTextField(
                value = code,
                onValueChange = { if (it.length <= 6) code = it },
                label = { Text("Código de 6 dígitos") },
                modifier = Modifier.fillMaxWidth(if (isPortrait) 1f else 0.4f)
            )

            message?.let {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = it,
                    color = if (isError) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary
                )
            }

            Spacer(modifier = Modifier.height(32.dp))

            if (isLoading) {
                CircularProgressIndicator()
            } else {
                Button(
                    onClick = {
                        if (code.length < 6) {
                            message = "Insira o código de 6 dígitos"
                            isError = true
                            return@Button
                        }

                        isLoading = true
                        message = null
                        
                        scope.launch {
                            try {
                                val response = apiService.verifyMfa(MfaRequest(numUtente, code))
                                if (response.isSuccessful && response.body()?.success == true) {
                                    onMfaSuccess()
                                } else {
                                    message = response.body()?.message ?: "Código inválido ou expirado"
                                    isError = true
                                }
                            } catch (e: Exception) {
                                message = "Erro de conexão: ${e.localizedMessage}"
                                isError = true
                            } finally {
                                isLoading = false
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth(if (isPortrait) 1f else 0.4f)
                ) {
                    Text("Verificar")
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            TextButton(onClick = {
                isLoading = true
                message = null
                scope.launch {
                    try {
                        val response = apiService.recoverAccess(numUtente)
                        if (response.isSuccessful && response.body()?.success == true) {
                            message = "Novo PIN enviado com sucesso!"
                            isError = false
                        } else {
                            message = response.body()?.message ?: "Erro ao reenviar PIN"
                            isError = true
                        }
                    } catch (e: Exception) {
                        message = "Erro de conexão: ${e.localizedMessage}"
                        isError = true
                    } finally {
                        isLoading = false
                    }
                }
            }) {
                Text("Esqueceu o PIN? Reenviar novo PIN")
            }

            TextButton(onClick = onNavigateBack) {
                Text("Cancelar")
            }
        }
    }
}
