# Spoty Ad X

Mutes Spoty while an ad plays and restores the sound when music returns.

## Download

Go to the [latest release](../../releases/latest) and download:

- **SpotyAdX.exe** for Windows (no install, just run it)
- **SpotyAdX.apk** for Android (allow "install unknown apps" when asked)

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
    pyinstaller --onefile --noconsole --name SpotyAdX windows/ad_muter.pyw

- Android: `cd android-app && npm ci && npx expo prebuild -p android --no-install && cd android && ./gradlew assembleRelease`

GitHub Actions builds and publishes the exe and apk on every push to `main`.

## Notes

This project is not affiliated with Spoty. It may break its terms of service; use at your own risk.
