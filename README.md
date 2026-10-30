# Spoty Ad X

Mutes Spoty while an ad plays and restores the sound when music returns. Windows version.

## Download

Go to the [latest release](../../releases/latest) and download **SpotyAdX.exe**. No install needed, just run it.

## How it works

Reads Spoty's window title and Windows media info. Anything that is not "Artist - Song" counts as an ad.
Only Spoty is muted. No login needed. Minimize the window to keep it running; closing it stops it.

## Build from source

    pip install -r windows/requirements.txt pyinstaller
    pyinstaller --onefile --noconsole --name SpotyAdX windows/ad_muter.pyw

GitHub Actions builds and publishes the exe on every push to `main`.

## Notes

This project is not affiliated with Spoty. It may break its terms of service; use at your own risk.
