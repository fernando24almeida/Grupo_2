package com.hospital.urgencias

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import com.hospital.urgencias.ui.admin.AdminDashboardScreen
import com.hospital.urgencias.ui.admin.AdminUniversalViewModel
import com.hospital.urgencias.ui.theme.HospitalTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    
    private val viewModel: AdminUniversalViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            HospitalTheme {
                AdminDashboardScreen(viewModel = viewModel)
            }
        }
    }
}
