package com.example.app_utente.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.example.app_utente.network.NetworkModule
import com.example.app_utente.security.SecurityUtils
import kotlinx.coroutines.launch

import com.example.app_utente.model.MfaRequest
import com.example.app_utente.model.RecoverRequest

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
    val context = LocalContext.current

    ResponsiveLayout { isPortrait ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Icon(
                imageVector = Icons.Default.Lock,
                contentDescription = null,
                modifier = Modifier.size(64.dp),
                tint = MaterialTheme.colorScheme.primary
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Text(
                text = "Segundo Fator", 
                style = MaterialTheme.typography.headlineLarge,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary
            )
            Text(
                text = "Insira o código de segurança", 
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.secondary
            )
            
            Spacer(modifier = Modifier.height(32.dp))

            OutlinedTextField(
                value = code,
                onValueChange = { if (it.length <= 6) code = it },
                label = { Text("Código MFA") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth(if (isPortrait) 1f else 0.4f),
                singleLine = true
            )

            if (message != null) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = message!!,
                    color = if (isError) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary,
                    style = MaterialTheme.typography.bodySmall
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
                                    response.body()?.data?.token?.trim()?.let { token ->
                                        SecurityUtils.saveToken(context, token)
                                        NetworkModule.authToken = token
                                    }
                                    onMfaSuccess()
                                } else {
                                    message = response.body()?.message ?: "Código inválido ou expirado"
                                    isError = true
                                }
                            } catch (e: Exception) {
                                message = "Erro de conexão"
                                isError = true
                            } finally {
                                isLoading = false
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth(if (isPortrait) 1f else 0.4f),
                    contentPadding = PaddingValues(16.dp)
                ) {
                    Text("VERIFICAR", fontWeight = FontWeight.Bold)
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            TextButton(onClick = {
                isLoading = true
                message = null
                scope.launch {
                    try {
                        val response = apiService.recoverAccess(RecoverRequest(numUtente))
                        if (response.isSuccessful) {
                            val apiResponse = response.body()
                            if (apiResponse?.success == true) {
                                message = "Novo PIN enviado para o seu email!"
                                isError = false
                            } else {
                                message = apiResponse?.message ?: "Erro ao reenviar PIN"
                                isError = true
                            }
                        } else {
                            message = "Erro ao reenviar PIN"
                            isError = true
                        }
                    } catch (e: Exception) {
                        message = "Erro de conexão"
                        isError = true
                    } finally {
                        isLoading = false
                    }
                }
            }) {
                Text("Não recebeu o código? Reenviar PIN")
            }

            TextButton(onClick = onNavigateBack) {
                Text("Voltar")
            }
        }
    }
}
