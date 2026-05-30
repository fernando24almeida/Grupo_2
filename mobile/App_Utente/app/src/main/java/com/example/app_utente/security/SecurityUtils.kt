package com.example.app_utente.security

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

object SecurityUtils {
    private const val PREFS_NAME = "secure_prefs"

    fun getEncryptedPrefs(context: Context) = EncryptedSharedPreferences.create(
        context,
        PREFS_NAME,
        MasterKey.Builder(context).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build(),
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    fun saveToken(context: Context, token: String) {
        getEncryptedPrefs(context).edit().putString("auth_token", token).apply()
    }

    fun getToken(context: Context): String? {
        return getEncryptedPrefs(context).getString("auth_token", null)
    }

    fun saveUserName(context: Context, name: String) {
        getEncryptedPrefs(context).edit().putString("user_name", name).apply()
    }

    fun getUserName(context: Context): String? {
        return getEncryptedPrefs(context).getString("user_name", null)
    }

    fun clearToken(context: Context) {
        getEncryptedPrefs(context).edit()
            .remove("auth_token")
            .remove("user_name")
            .apply()
    }
}
