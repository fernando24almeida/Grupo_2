package com.example.app_utente.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.example.app_utente.model.LoginRequest
import com.example.app_utente.network.NetworkModule
import kotlinx.coroutines.launch

@Composable
fun LoginScreen(
    onLoginSuccess: (String, Boolean) -> Unit, // numUtente, mfaRequired
    onNavigateToRegister: () -> Unit,
    onNavigateToRecover: () -> Unit
) {
    var numUtente by remember { mutableStateOf("") }
    var pin by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf<String?>(null) }

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
            Text(text = "Acesso Utente", style = MaterialTheme.typography.headlineLarge)
            Spacer(modifier = Modifier.height(32.dp))

            OutlinedTextField(
                value = numUtente,
                onValueChange = { numUtente = it },
                label = { Text("Nº Utente") },
                modifier = Modifier.fillMaxWidth(if (isPortrait) 1f else 0.6f)
            )

            Spacer(modifier = Modifier.height(16.dp))

            OutlinedTextField(
                value = pin,
                onValueChange = { pin = it },
                label = { Text("PIN / Senha") },
                visualTransformation = PasswordVisualTransformation(),
                modifier = Modifier.fillMaxWidth(if (isPortrait) 1f else 0.6f)
            )

            errorMessage?.let {
                Spacer(modifier = Modifier.height(8.dp))
                Text(text = it, color = MaterialTheme.colorScheme.error)
            }

            Spacer(modifier = Modifier.height(32.dp))

            if (isLoading) {
                CircularProgressIndicator()
            } else {
                Button(
                    onClick = {
                        if (numUtente.isBlank() || pin.isBlank()) {
                            errorMessage = "Preencha todos os campos"
                            return@Button
                        }
                        
                        isLoading = true
                        errorMessage = null
                        
                        scope.launch {
                            try {
                                val response = apiService.login(LoginRequest(numUtente, pin))
                                if (response.isSuccessful) {
                                    val apiResponse = response.body()
                                    if (apiResponse?.success == true && apiResponse.data != null) {
                                        onLoginSuccess(numUtente, apiResponse.data.mfaRequired)
                                    } else {
                                        errorMessage = apiResponse?.message ?: "Erro no login"
                                    }
                                } else {
                                    errorMessage = "Nº Utente ou PIN inválidos"
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
                    Text("Entrar")
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            TextButton(onClick = onNavigateToRegister) {
                Text("Não tem conta? Registe-se aqui")
            }

            TextButton(onClick = onNavigateToRecover) {
                Text("Esqueceu-se do PIN?")
            }
        }
    }
}
