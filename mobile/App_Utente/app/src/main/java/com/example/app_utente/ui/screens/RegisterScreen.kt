package com.example.app_utente.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.example.app_utente.model.RegisterRequest
import com.example.app_utente.network.NetworkModule
import kotlinx.coroutines.launch

@Composable
fun RegisterScreen(
    onRegisterSuccess: () -> Unit,
    onNavigateBack: () -> Unit
) {
    var numUtente by remember { mutableStateOf("") }
    var nome by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var pin by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf<String?>(null) }

    val scope = rememberCoroutineScope()
    val apiService = NetworkModule.apiService

    ResponsiveLayout { isPortrait ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = "Novo Registo", 
                style = MaterialTheme.typography.headlineLarge,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary
            )
            Text(
                text = "Crie a sua conta de utente", 
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.secondary
            )
            
            Spacer(modifier = Modifier.height(32.dp))

            OutlinedTextField(
                value = numUtente,
                onValueChange = { numUtente = it },
                label = { Text("Nº de Utente") },
                leadingIcon = { Icon(Icons.Default.AccountBox, contentDescription = null) },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth(if (isPortrait) 1f else 0.6f),
                singleLine = true
            )

            Spacer(modifier = Modifier.height(16.dp))

            OutlinedTextField(
                value = nome,
                onValueChange = { nome = it },
                label = { Text("Nome Completo") },
                leadingIcon = { Icon(Icons.Default.Person, contentDescription = null) },
                modifier = Modifier.fillMaxWidth(if (isPortrait) 1f else 0.6f),
                singleLine = true
            )

            Spacer(modifier = Modifier.height(16.dp))

            OutlinedTextField(
                value = email,
                onValueChange = { email = it },
                label = { Text("Email") },
                leadingIcon = { Icon(Icons.Default.Email, contentDescription = null) },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                modifier = Modifier.fillMaxWidth(if (isPortrait) 1f else 0.6f),
                singleLine = true
            )

            Spacer(modifier = Modifier.height(16.dp))

            OutlinedTextField(
                value = pin,
                onValueChange = { pin = it },
                label = { Text("Definir PIN") },
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
                        val trimmedNome = nome.trim()
                        val trimmedEmail = email.trim()
                        val trimmedPin = pin.trim()

                        if (trimmedNumUtente.isBlank() || trimmedNome.isBlank() || trimmedEmail.isBlank() || trimmedPin.isBlank()) {
                            errorMessage = "Preencha todos os campos"
                            return@Button
                        }

                        isLoading = true
                        errorMessage = null

                        scope.launch {
                            try {
                                val response = apiService.register(
                                    RegisterRequest(trimmedNumUtente, trimmedNome, trimmedPin, trimmedEmail)
                                )
                                if (response.isSuccessful && response.body()?.success == true) {
                                    onRegisterSuccess()
                                } else {
                                    errorMessage = response.body()?.message ?: "Erro no registo"
                                }
                            } catch (e: Exception) {
                                errorMessage = "Erro de conexão"
                            } finally {
                                isLoading = false
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth(if (isPortrait) 1f else 0.4f),
                    contentPadding = PaddingValues(16.dp)
                ) {
                    Text("REGISTAR", fontWeight = FontWeight.Bold)
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            TextButton(onClick = onNavigateBack) {
                Text("Já tem conta? Voltar ao Login")
            }
        }
    }
}
