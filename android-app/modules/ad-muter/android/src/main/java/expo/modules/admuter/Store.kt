package expo.modules.admuter

import android.content.Context
import android.content.SharedPreferences
import android.media.AudioManager
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

object Store {
  fun prefs(c: Context): SharedPreferences =
    c.getSharedPreferences("admuter", Context.MODE_PRIVATE)

  @Synchronized
  fun log(c: Context, msg: String) {
    val p = prefs(c)
    val old = p.getString("log", "") ?: ""
    val line = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.US).format(Date()) + "  " + msg
    var all = if (old.isEmpty()) line else old + "\n" + line
    if (all.length > 60000) {
      all = all.takeLast(50000)
      val nl = all.indexOf('\n')
      if (nl >= 0) all = all.substring(nl + 1)
    }
    p.edit().putString("log", all).apply()
  }

  @Synchronized
  fun setMuted(c: Context, mute: Boolean) {
    val am = c.getSystemService(Context.AUDIO_SERVICE) as AudioManager
    val p = prefs(c)
    val muted = p.getBoolean("muted", false)
    if (mute && !muted) {
      val v = am.getStreamVolume(AudioManager.STREAM_MUSIC)
      p.edit().putInt("prevVol", v).putBoolean("muted", true).apply()
      try {
        am.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_MUTE, 0)
      } catch (e: Exception) {
        log(c, "ADJUST_MUTE failed: " + e.message)
      }
      try {
        am.setStreamVolume(AudioManager.STREAM_MUSIC, 0, 0)
      } catch (e: Exception) {
        log(c, "setStreamVolume failed: " + e.message)
      }
      log(c, "Mute applied: volume was $v, now " + am.getStreamVolume(AudioManager.STREAM_MUSIC) +
        ", stream muted=" + am.isStreamMute(AudioManager.STREAM_MUSIC))
    } else if (!mute && muted) {
      val prev = p.getInt("prevVol", 5)
      try {
        am.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0)
      } catch (e: Exception) {
        log(c, "ADJUST_UNMUTE failed: " + e.message)
      }
      try {
        am.setStreamVolume(AudioManager.STREAM_MUSIC, prev, 0)
      } catch (e: Exception) {
        log(c, "setStreamVolume failed: " + e.message)
      }
      p.edit().putBoolean("muted", false).apply()
      log(c, "Unmute applied: volume now " + am.getStreamVolume(AudioManager.STREAM_MUSIC) +
        ", stream muted=" + am.isStreamMute(AudioManager.STREAM_MUSIC))
    }
  }
}
