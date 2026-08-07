package com.klmub.mubvpn

import android.content.Intent
import android.service.quicksettings.TileService
import android.service.quicksettings.Tile
import android.os.Build

/**
 * VpnTileService provides a Quick Settings Tile to toggle the VPN connection.
 * It communicates with [MainActivity] via broadcasts to trigger VPN state changes.
 */
class VpnTileService : TileService() {

    /**
     * Called when the user taps on the Quick Settings Tile.
     * Sends a broadcast to toggle the VPN and attempts to close the system dialogs (notification shade).
     */
    override fun onClick() {
        super.onClick()
        
        // Сигнал жөнөтөбүз (Broadcast) / Send a broadcast signal
        val intent = Intent("com.klmub.mubvpn.TOGGLE_VPN").apply {
            `package` = packageName
        }
        sendBroadcast(intent)
        
        // Панелди жаап коёбуз (кошумча) / Close the panel (optional)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            // Android 14+ үчүн панелди жабуу талап кылынбайт же башкача жасалат
            // For Android 14+, closing the panel is either not required or handled differently.
        } else {
            @Suppress("DEPRECATION")
            val closeIntent = Intent(Intent.ACTION_CLOSE_SYSTEM_DIALOGS)
            sendBroadcast(closeIntent)
        }
    }

    /**
     * Called when the tile is added to the Quick Settings or becomes visible.
     * Triggers an update of the tile's visual state.
     */
    override fun onStartListening() {
        super.onStartListening()
        updateTileState()
    }

    /**
     * Updates the tile's state (Active/Inactive) and label based on the current VPN connection status
     * stored in SharedPreferences.
     */
    private fun updateTileState() {
        val tile = qsTile ?: return
        val prefs = getSharedPreferences("VPN_STATE", MODE_PRIVATE)
        val isConnected = prefs.getBoolean("is_connected", false)
        
        tile.state = if (isConnected) Tile.STATE_ACTIVE else Tile.STATE_INACTIVE
        tile.label = if (isConnected) "mubVPN (On)" else "mubVPN"
        tile.updateTile()
    }
}
