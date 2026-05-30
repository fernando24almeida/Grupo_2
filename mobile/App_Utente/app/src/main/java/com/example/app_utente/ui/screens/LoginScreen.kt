package com.example.app_utente.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AccountCircle
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.app_utente.model.LoginRequest
import com.example.app_utente.network.NetworkModule
import com.example.app_utente.security.SecurityUtils
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
                imageVector = Icons.Default.AccountCircle,
                contentDescription = null,
                modifier = Modifier.size(80.dp),
                tint = MaterialTheme.colorScheme.primary
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Text(
                text = "Portal do Utente", 
                style = MaterialTheme.typography.headlineLarge,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary
            )
            Text(
                text = "Acesso às suas Urgências", 
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.secondary
            )
            
            Spacer(modifier = Modifier.height(48.dp))

            OutlinedTextField(
                value = numUtente,
                onValueChange = { numUtente = it },
                label = { Text("Nº de Utente") },
                leadingIcon = { Icon(Icons.Default.AccountCircle, contentDescription = null) },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth(if (isPortrait) 1f else 0.6f),
                singleLine = true
            )

            Spacer(modifier = Modifier.height(16.dp))

            OutlinedTextField(
                value = pin,
                onValueChange = { pin = it },
                label = { Text("PIN de Acesso") },
                leadingIcon = { Icon(Icons.Default.Lock, contentDescription = null) },
                visualTransformation = PasswordVisualTransformation(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
                modifier = Modifier.fillMaxWidth(if (isPortrait) 1f else 0.6f),
                singleLine = true
            )

            if (errorMessage != null) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = errorMessage!!, 
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodySmall
                )
            }

            Spacer(modifier = Modifier.height(32.dp))

            if (isLoading) {
                CircularProgressIndicator()
            } else {
                Button(
                    onClick = {
                        val trimmedNumUtente = numUtente.trim()
                        val trimmedPin = pin.trim()
                        
                        if (trimmedNumUtente.isBlank() || trimmedPin.isBlank()) {
                            errorMessage = "Preencha todos os campos"
                            return@Button
                        }
                        
                        isLoading = true
                        errorMessage = null
                        
                        scope.launch {
                            try {
                                val response = apiService.login(LoginRequest(trimmedNumUtente, trimmedPin))
                                if (response.isSuccessful) {
                                    val apiResponse = response.body()
                                    if (apiResponse?.success == true && apiResponse.data != null) {
                                        val token = apiResponse.data.token.trim()
                                        val name = apiResponse.data.utente?.nome ?: ""
                                        SecurityUtils.saveToken(context, token)
                                        SecurityUtils.saveUserName(context, name)
                                        NetworkModule.authToken = token
                                        onLoginSuccess(trimmedNumUtente, apiResponse.data.mfaRequired)
                                    } else {
                                        errorMessage = apiResponse?.message ?: "Credenciais inválidas"
                                    }
                                } else {
                                    errorMessage = "Nº Utente ou PIN incorretos"
                                }
                            } catch (e: Exception) {
                                errorMessage = "Erro ao contactar o servidor"
                            } finally {
                                isLoading = false
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth(if (isPortrait) 1f else 0.4f),
                    contentPadding = PaddingValues(16.dp)
                ) {
                    Text("ENTRAR", fontWeight = FontWeight.Bold)
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            TextButton(onClick = onNavigateToRegister) {
                Text("Não tem conta? Registe-se aqui")
            }

            TextButton(onClick = onNavigateToRecover) {
                Text("Esqueceu-se do PIN?")
            }
        }
    }
}
