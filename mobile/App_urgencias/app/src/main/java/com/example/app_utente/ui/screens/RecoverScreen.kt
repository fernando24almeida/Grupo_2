package com.example.app_utente.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.app_utente.network.NetworkModule
import kotlinx.coroutines.launch

@Composable
fun RecoverScreen(
    onRecoverRequested: () -> Unit,
    onNavigateBack: () -> Unit
) {
    var numUtente by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    var successMessage by remember { mutableStateOf<String?>(null) }

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
            Text(text = "Recuperar Acesso", style = MaterialTheme.typography.headlineLarge)
            Spacer(modifier = Modifier.height(16.dp))
            Text(text = "Insira o seu Nº de Utente para recuperar o acesso.")
            Spacer(modifier = Modifier.height(32.dp))

            OutlinedTextField(
                value = numUtente,
                onValueChange = { numUtente = it },
                label = { Text("Nº Utente") },
                modifier = Modifier.fillMaxWidth(if (isPortrait) 1f else 0.6f)
            )

            errorMessage?.let {
                Spacer(modifier = Modifier.height(8.dp))
                Text(text = it, color = MaterialTheme.colorScheme.error)
            }

            successMessage?.let {
                Spacer(modifier = Modifier.height(8.dp))
                Text(text = it, color = MaterialTheme.colorScheme.primary)
            }

            Spacer(modifier = Modifier.height(32.dp))

            if (isLoading) {
                CircularProgressIndicator()
            } else {
                Button(
                    onClick = {
                        if (numUtente.isBlank()) {
                            errorMessage = "Insira o seu Nº de Utente"
                            return@Button
                        }

                        isLoading = true
                        errorMessage = null
                        successMessage = null

                        scope.launch {
                            try {
                                val response = apiService.recoverAccess(numUtente)
                                if (response.isSuccessful) {
                                    val apiResponse = response.body()
                                    if (apiResponse?.success == true) {
                                        successMessage = "Novo PIN enviado com sucesso!"
                                        // Optional: wait a bit and go back
                                    } else {
                                        errorMessage = apiResponse?.message ?: "Erro ao recuperar acesso"
                                    }
                                } else {
                                    errorMessage = "Nº Utente inválido ou erro no servidor"
                                }
                            } catch (e: Exception) {
                                errorMessage = "Erro de conexão: ${e.localizedMessage}"
                            } finally {
                                isLoading = false
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth(if (isPortrait) 1f else 0.4f)
                ) {
                    Text("Recuperar")
                }
            }

            TextButton(onClick = onNavigateBack) {
                Text("Voltar ao Login")
            }
        }
    }
}
