package expo.modules.admuter

import android.app.Notification
import android.os.Handler
import android.os.Looper
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification

class AdListenerService : NotificationListenerService() {
  private val spotify = "com.spotify.music"

  override fun onListenerConnected() {
    Store.log(this, "Notification access connected")
    try {
      activeNotifications?.forEach { handle(it) }
    } catch (e: Exception) {
      Store.log(this, "Error reading notifications: " + e.message)
    }
  }

  override fun onNotificationPosted(sbn: StatusBarNotification?) {
    handle(sbn)
  }

  override fun onNotificationRemoved(sbn: StatusBarNotification?) {
    if (sbn?.packageName != spotify) return
    Handler(Looper.getMainLooper()).postDelayed({
      try {
        val still = activeNotifications?.any { it.packageName == spotify } ?: false
        if (!still && Store.prefs(this).getBoolean("muted", false)) {
          Store.setMuted(this, false)
          Store.log(this, "Spoty notification gone - unmuted")
        }
      } catch (e: Exception) {
      }
    }, 2500)
  }

  private fun isAd(title: String, text: String): Boolean {
    val t = title.trim().lowercase()
    val x = text.trim().lowercase()
    return t == "advertisement" || x.contains("advertisement") || t == "spotify" || x == "spotify" ||
      t == "—" || t == "-"
  }

  private fun handle(sbn: StatusBarNotification?) {
    if (sbn == null || sbn.packageName != spotify) return
    val p = Store.prefs(this)
    val extras = sbn.notification.extras
    val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString() ?: ""
    val text = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString() ?: ""
    val key = "$title|$text"
    if (key == p.getString("lastKey", "")) return
    p.edit().putString("lastKey", key).putString("lastTitle", title).putString("lastText", text).apply()
    Store.log(this, "NOW PLAYING: title='$title' text='$text'")

    if (!p.getBoolean("enabled", true)) return
    val ad = isAd(title, text)
    val wasMuted = p.getBoolean("muted", false)
    if (ad && !wasMuted) {
      p.edit().putInt("ads", p.getInt("ads", 0) + 1).apply()
      Store.setMuted(this, true)
      Store.log(this, "AD detected - muted")
    } else if (!ad && wasMuted) {
      Store.setMuted(this, false)
      Store.log(this, "Music - unmuted")
    }
  }
}
