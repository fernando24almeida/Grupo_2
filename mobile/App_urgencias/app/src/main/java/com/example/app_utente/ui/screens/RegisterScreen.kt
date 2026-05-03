package com.example.app_utente.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp

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

    ResponsiveLayout { isPortrait ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(text = "Registo de Utente", style = MaterialTheme.typography.headlineLarge)
            Spacer(modifier = Modifier.height(32.dp))

            OutlinedTextField(
                value = numUtente,
                onValueChange = { numUtente = it },
                label = { Text("Nº Utente") },
                modifier = Modifier.fillMaxWidth(if (isPortrait) 1f else 0.6f)
            )

            Spacer(modifier = Modifier.height(16.dp))

            OutlinedTextField(
                value = nome,
                onValueChange = { nome = it },
                label = { Text("Nome Completo") },
                modifier = Modifier.fillMaxWidth(if (isPortrait) 1f else 0.6f)
            )

            Spacer(modifier = Modifier.height(16.dp))

            OutlinedTextField(
                value = email,
                onValueChange = { email = it },
                label = { Text("Email") },
                modifier = Modifier.fillMaxWidth(if (isPortrait) 1f else 0.6f)
            )

            Spacer(modifier = Modifier.height(16.dp))

            OutlinedTextField(
                value = pin,
                onValueChange = { pin = it },
                label = { Text("Definir PIN") },
                visualTransformation = PasswordVisualTransformation(),
                modifier = Modifier.fillMaxWidth(if (isPortrait) 1f else 0.6f)
            )

            Spacer(modifier = Modifier.height(32.dp))

            if (isLoading) {
                CircularProgressIndicator()
            } else {
                Button(
                    onClick = {
                        isLoading = true
                        // Call Register API
                        onRegisterSuccess()
                    },
                    modifier = Modifier.fillMaxWidth(if (isPortrait) 1f else 0.4f)
                ) {
                    Text("Registar")
                }
            }

            TextButton(onClick = onNavigateBack) {
                Text("Voltar ao Login")
            }
        }
    }
}
