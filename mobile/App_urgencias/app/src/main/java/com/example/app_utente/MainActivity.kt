package com.example.app_utente

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.Composable
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.example.app_utente.ui.screens.*
import com.example.app_utente.ui.theme.AppUtenteTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            AppUtenteTheme {
                AppNavigation()
            }
        }
    }
}

@Composable
fun AppNavigation() {
    val navController = rememberNavController()

    NavHost(navController = navController, startDestination = "login") {
        composable("login") {
            LoginScreen(
                onLoginSuccess = { numUtente, mfaRequired ->
                    if (mfaRequired) {
                        navController.navigate("mfa/$numUtente")
                    } else {
                        navController.navigate("dashboard/$numUtente") {
                            popUpTo("login") { inclusive = true }
                        }
                    }
                },
                onNavigateToRegister = { navController.navigate("register") },
                onNavigateToRecover = { navController.navigate("recover") }
            )
        }
        composable("register") {
            RegisterScreen(
                onRegisterSuccess = {
                    navController.navigate("login") {
                        popUpTo("register") { inclusive = true }
                    }
                },
                onNavigateBack = { navController.popBackStack() }
            )
        }
        composable("mfa/{numUtente}") { backStackEntry ->
            val numUtente = backStackEntry.arguments?.getString("numUtente") ?: ""
            MfaScreen(
                numUtente = numUtente,
                onMfaSuccess = {
                    navController.navigate("dashboard/$numUtente") {
                        popUpTo("login") { inclusive = true }
                    }
                },
                onNavigateBack = { navController.popBackStack() },
                onNavigateToRecover = { navController.navigate("recover") }
            )
        }
        composable("recover") {
            RecoverScreen(
                onRecoverRequested = {
                    navController.navigate("login") {
                        popUpTo("recover") { inclusive = true }
                    }
                },
                onNavigateBack = { navController.popBackStack() }
            )
        }
        composable("dashboard/{numUtente}") { backStackEntry ->
            val numUtente = backStackEntry.arguments?.getString("numUtente") ?: ""
            DashboardScreen(
                numUtente = numUtente,
                onLogout = {
                    navController.navigate("login") {
                        popUpTo("dashboard") { inclusive = true }
                    }
                }
            )
        }
    }
}
