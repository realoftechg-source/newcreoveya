# Creoveya Desktop App

A native Windows wrapper around your live site (https://creoveya.onrender.com)
built with [pywebview](https://pywebview.flowrl.com/). Completely
independent of the Django project — doesn't import or modify any Django
code, just opens a native window pointed at your hosted site.

## What's in here

```
desktop/
├── app.py              — pywebview wrapper (splash screen, error handling, retry)
├── installer.iss        — Inno Setup script: builds a real installer with
│                           Start Menu + Desktop shortcuts and an uninstaller
├── requirements.txt      — pywebview, pyinstaller, requests
└── assets/
    ├── icon.ico            — multi-resolution Windows icon (16–256px)
    └── icon.png             — 256x256 PNG reference copy
```

## Running it locally (to test before building)

```powershell
cd desktop
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

## Building the installer manually (fallback if not using GitHub Actions)

Two tools needed: **PyInstaller** (already in requirements.txt) and
**[Inno Setup](https://jrsoftware.org/isdl.php)** (free, install it on
your Windows PC first).

```powershell
cd desktop

REM 1. Build the app folder (onedir — more stable startup than onefile)
pyinstaller --onedir --windowed --name Creoveya --icon assets/icon.ico --add-data "assets;assets" app.py

REM 2. Package it into a real installer with shortcuts
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

The finished installer is `desktop/Output/CreoveyaSetup.exe`. Running it
installs to Program Files, adds a **Start Menu shortcut** and a
**Desktop shortcut** (both using your app icon), and includes a proper
uninstaller — exactly like installing any normal Windows app.

## Why an installer instead of a bare .exe

A raw `--onefile` PyInstaller `.exe` run directly does **not** create any
shortcuts, and re-extracts itself into a temp folder on every launch
(slower, and can look "Not Responding" briefly on slower disks or with
antivirus scanning). Switching to `--onedir` + a proper Inno Setup
installer fixes both: faster, more reliable startup, and real Windows
install behavior (shortcuts, uninstaller, Programs list entry).

## About "Not Responding" on first launch

If the app briefly shows "Not Responding" in Task Manager right after
opening, this is almost always one of two things:
1. **Cold start** — Render's free tier can take 30-60s to wake up after
   inactivity. The splash screen polls in a background thread, so the
   window itself should stay responsive — if it doesn't, see #2.
2. **Missing WebView2 Runtime** — pywebview's Windows backend depends on
   the Microsoft Edge WebView2 Runtime. Most Windows 10/11 PCs have it
   pre-installed, but older or locked-down machines might not. `app.py`
   now shows a native error message box pointing users to the official
   installer (`https://developer.microsoft.com/microsoft-edge/webview2/`)
   if this happens, instead of just hanging silently.

## About the icon

`static/img/logo-mark.svg` from your uploaded project (a geometric mark
in your teal/copper brand colors) was converted into a proper
multi-resolution `.ico`. If you have a separate official logo file,
just replace `desktop/assets/icon.ico` (same multi-res format) and
rebuild — nothing else needs to change.
