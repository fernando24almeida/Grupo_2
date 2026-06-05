package com.hospital.urgencias.ui.admin

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.hospital.urgencias.domain.model.User

@Composable
fun UserListItem(user: User, onToggle: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Row(
            modifier = Modifier.padding(16.dp).fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column {
                Text(user.username, style = MaterialTheme.typography.titleMedium)
                Text(user.role, style = MaterialTheme.typography.bodySmall)
            }
            Switch(
                checked = user.isActive,
                onCheckedChange = { onToggle() }
            )
        }
    }
}
