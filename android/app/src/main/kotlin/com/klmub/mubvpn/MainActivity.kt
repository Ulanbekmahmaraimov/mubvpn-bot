package com.klmub.mubvpn

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.os.Build
import android.service.quicksettings.TileService
import androidx.core.content.edit
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity: FlutterActivity() {
    private val channelName = "com.klmub.mubvpn/tile"
    private val notificationChannelName = "com.klmub.mubvpn/notifications"
    
    private var methodChannel: MethodChannel? = null
    private var notificationChannel: MethodChannel? = null
    private var isDartReady = false
    private var pendingToggle = false
    private var permissionResult: MethodChannel.Result? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        methodChannel = MethodChannel(flutterEngine.dartExecutor.binaryMessenger, channelName)
        notificationChannel = MethodChannel(flutterEngine.dartExecutor.binaryMessenger, notificationChannelName)
        
        // Системалык билдирүү каналын түзүү (Ключ чыгышы үчүн өтө маанилүү)
        createNotificationChannel()

        methodChannel?.setMethodCallHandler { call, result ->
            when (call.method) {
                "ready" -> {
                    isDartReady = true
                    if (pendingToggle) {
                        methodChannel?.invokeMethod("toggleVpn", null)
                        pendingToggle = false
                    }
                    result.success(null)
                }
                "updateTileStatus" -> {
                    val isConnected = call.argument<Boolean>("isConnected") ?: false
                    saveVpnState(isConnected)
                    updateTile()
                    result.success(null)
                }
                else -> result.notImplemented()
            }
        }

        notificationChannel?.setMethodCallHandler { call, result ->
            if (call.method == "requestNotificationPermission") {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                    if (checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                        permissionResult = result
                        requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 101)
                    } else {
                        result.success(true)
                    }
                } else {
                    result.success(true)
                }
            } else {
                result.notImplemented()
            }
        }

        val filter = IntentFilter("com.klmub.mubvpn.TOGGLE_VPN")
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(tileReceiver, filter, RECEIVER_EXPORTED)
        } else {
            @Suppress("UnspecifiedRegisterReceiverFlag")
            registerReceiver(tileReceiver, filter)
        }

        handleIntent(intent)
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val name = "mubVPN Service"
            val descriptionText = "VPN Connection Status"
            val importance = NotificationManager.IMPORTANCE_LOW
            val channel = NotificationChannel("flutter_v2ray_channel", name, importance).apply {
                description = descriptionText
            }
            val notificationManager: NotificationManager =
                getSystemService(NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.createNotificationChannel(channel)
        }
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == 101) {
            permissionResult?.success(grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED)
            permissionResult = null
        }
    }

    private val tileReceiver = object : android.content.BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent?.action == "com.klmub.mubvpn.TOGGLE_VPN") {
                if (isDartReady) {
                    methodChannel?.invokeMethod("toggleVpn", null)
                } else {
                    val launchIntent = context?.packageManager?.getLaunchIntentForPackage(context.packageName)
                    launchIntent?.let {
                        it.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        it.action = "ACTION_TOGGLE_VPN"
                        context.startActivity(it)
                    }
                }
            }
        }
    }

    private fun handleIntent(intent: Intent?) {
        if (intent?.action == "ACTION_TOGGLE_VPN") {
            if (isDartReady) {
                methodChannel?.invokeMethod("toggleVpn", null)
            } else {
                pendingToggle = true
            }
        }
    }

    override fun onDestroy() {
        try {
            unregisterReceiver(tileReceiver)
        } catch (_: Exception) {}
        super.onDestroy()
    }

    private fun saveVpnState(isConnected: Boolean) {
        val prefs = getSharedPreferences("VPN_STATE", MODE_PRIVATE)
        prefs.edit {
            putBoolean("is_connected", isConnected)
        }
    }

    private fun updateTile() {
        TileService.requestListeningState(this, ComponentName(this, VpnTileService::class.java))
    }
}
