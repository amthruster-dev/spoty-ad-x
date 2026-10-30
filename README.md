# Spoty Ad X

Mutes Spoty while an ad plays and restores the sound when music returns.

## Download

Open the [latest release](../../releases/latest) and download the file for your device.

### Windows

1. Download **SpotyAdX.exe** and double-click it.
2. If Windows shows "Windows protected your PC", click **More info**, then **Run anyway**.
   (The app isn't code-signed, so Windows warns about every new app like this.)
3. Open Spotify and play music. The app mutes Spotify's ads and unmutes when music returns.
4. Minimize the window to keep it running. Closing it stops it.

### Android

1. Download **SpotyAdX.apk** and open it. Allow "install unknown apps" for your browser when asked.
2. Open **Spoty Ad X** and tap **Open notification access**. Turn it on for Spoty Ad X.
3. If the switch is greyed out or says "Restricted setting": Settings, Apps, Spoty Ad X, tap the
   three dots, choose **Allow restricted settings**, then repeat step 2.
4. Settings, Apps, Spoty Ad X, Battery: set it to **Unrestricted** so Android doesn't stop it.
5. Play Spotify. The banner turns red and says AD - MUTED during ads.

Android can't mute a single app, so the phone's media volume goes to 0 during an ad and comes back after.

## Windows

Reads Spoty's window title and Windows media info. Anything that is not "Artist - Song" counts as an ad.
Only Spoty is muted. No login needed. Minimize the window to keep it running; closing it stops it.

## Android

An Expo (React Native) app with a small native notification listener (`android-app/`).
On first launch tap **Open notification access** and turn it on for Spoty Ad X. If the switch is
greyed out, open App info, tap the three dots, and choose "Allow restricted settings".
Android can't mute one app, so the app sets the phone's media volume to 0 during ads and restores it after.
Set Battery to Unrestricted to keep it running.

## Build from source

    pip install -r windows/requirements.txt pyinstaller
    pyinstaller --onefile --noconsole --name SpotyAdX --icon windows/icon.ico --add-data "windows/icon.ico;." windows/ad_muter.pyw

- Android: `cd android-app && npm ci && npx expo prebuild -p android --no-install && cd android && ./gradlew assembleRelease`

GitHub Actions builds and publishes the exe and apk on every push to `main`.

## Notes

This project is not affiliated with Spoty. It may break its terms of service; use at your own risk.
