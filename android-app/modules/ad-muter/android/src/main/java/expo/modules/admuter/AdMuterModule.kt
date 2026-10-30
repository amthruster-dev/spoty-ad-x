package expo.modules.admuter

import android.content.Intent
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition

class AdMuterModule : Module() {
  private val ctx get() = appContext.reactContext ?: throw Exception("No context")

  private fun listenerEnabled(): Boolean {
    val flat = Settings.Secure.getString(ctx.contentResolver, "enabled_notification_listeners") ?: ""
    return flat.contains(ctx.packageName)
  }

  override fun definition() = ModuleDefinition {
    Name("AdMuter")

    Function("isListenerEnabled") { listenerEnabled() }

    Function("openListenerSettings") {
      val i = Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)
      i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
      ctx.startActivity(i)
    }

    Function("openAppSettings") {
      val i = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
      i.data = android.net.Uri.parse("package:" + ctx.packageName)
      i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
      ctx.startActivity(i)
    }

    Function("getStatus") {
      val p = Store.prefs(ctx)
      mapOf(
        "listener" to listenerEnabled(),
        "enabled" to p.getBoolean("enabled", true),
        "muted" to p.getBoolean("muted", false),
        "ads" to p.getInt("ads", 0),
        "lastTitle" to (p.getString("lastTitle", "") ?: ""),
        "lastText" to (p.getString("lastText", "") ?: "")
      )
    }

    Function("setEnabled") { enabled: Boolean ->
      Store.prefs(ctx).edit().putBoolean("enabled", enabled).apply()
      if (!enabled) Store.setMuted(ctx, false)
      Store.log(ctx, if (enabled) "App started" else "App stopped")
    }

    Function("getLog") { Store.prefs(ctx).getString("log", "") ?: "" }

    Function("clearLog") {
      Store.prefs(ctx).edit().putString("log", "").putInt("ads", 0).apply()
    }

    Function("testMute") {
      Store.setMuted(ctx, true)
      Store.log(ctx, "TEST: muted for 3 seconds")
      Handler(Looper.getMainLooper()).postDelayed({
        Store.setMuted(ctx, false)
        Store.log(ctx, "TEST: unmuted")
      }, 3000)
    }
  }
}
