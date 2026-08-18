"""
Creoveya desktop wrapper.

Opens a native window that loads https://creoveya.onrender.com. Shows a
branded splash screen while the site connects (Render's free tier can
take 30-60s to wake up from a cold start), and a friendly error screen
with a Retry button if the connection fails.

This file does not touch the Django project at all — it's a completely
separate, standalone app that just points a native browser window at
your already-hosted site.
"""

import threading
import time

import requests
import webview

APP_TITLE = "Creoveya"
TARGET_URL = "https://creoveya.onrender.com"
MAX_WAIT_SECONDS = 90
CHECK_INTERVAL_SECONDS = 2

SPLASH_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body {
    margin: 0; height: 100%;
    background: radial-gradient(circle at 30% 20%, #12211f 0%, #0a0f0f 60%);
    display: flex; align-items: center; justify-content: center;
    font-family: -apple-system, 'Segoe UI', Arial, sans-serif; color: #eef2f1;
  }
  .wrap { text-align: center; }
  .spinner {
    width: 48px; height: 48px; margin: 0 auto 22px;
    border: 4px solid rgba(20,184,166,0.2);
    border-top-color: #14b8a6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  h1 {
    font-size: 24px; margin: 0 0 10px; font-weight: 800;
    background: linear-gradient(135deg, #14b8a6, #c2793d);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }
  p { color: #97a3a1; font-size: 14px; line-height: 1.6; margin: 0; }
</style>
</head>
<body>
  <div class="wrap">
    <div class="spinner"></div>
    <h1>Creoveya</h1>
    <p>Connecting to your live studio&hellip;<br>This can take up to a minute on first launch.</p>
  </div>
</body>
</html>
"""

ERROR_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body {
    margin: 0; height: 100%;
    background: #0a0f0f;
    display: flex; align-items: center; justify-content: center;
    font-family: -apple-system, 'Segoe UI', Arial, sans-serif; color: #eef2f1;
  }
  .wrap { text-align: center; max-width: 420px; padding: 20px; }
  h1 { color: #e2564d; font-size: 20px; margin-bottom: 10px; }
  p { color: #97a3a1; font-size: 14px; line-height: 1.6; }
  button {
    margin-top: 18px; padding: 10px 26px; border: none; border-radius: 8px;
    background: linear-gradient(135deg, #14b8a6, #c2793d); color: #fff;
    font-weight: 600; cursor: pointer; font-size: 14px;
  }
  button:hover { opacity: 0.9; }
</style>
</head>
<body>
  <div class="wrap">
    <h1>Unable to connect</h1>
    <p>We couldn't reach Creoveya. Please check your internet connection and try again.</p>
    <button onclick="window.pywebview.api.retry()">Retry</button>
  </div>
</body>
</html>
"""


class Api:
    """Exposed to the error page's Retry button via window.pywebview.api."""

    def __init__(self):
        self.window = None

    def retry(self):
        threading.Thread(target=connect_and_load, args=(self.window,), daemon=True).start()


def is_site_reachable(url):
    """A lightweight HEAD check — cheaper and faster than downloading the
    full page repeatedly while polling."""
    try:
        response = requests.head(url, timeout=6, allow_redirects=True)
        if response.status_code < 500:
            return True
    except requests.RequestException:
        pass

    # Some hosts don't support HEAD well — fall back to a real GET before
    # giving up on this attempt.
    try:
        response = requests.get(url, timeout=8)
        return response.status_code < 500
    except requests.RequestException:
        return False


def connect_and_load(window):
    """Polls the live site until it responds, then swaps the splash
    screen for the real app. Falls back to the error screen if the site
    never comes up within MAX_WAIT_SECONDS. Any unexpected exception here
    also falls back to the error screen instead of leaving the splash
    screen frozen forever."""
    try:
        start_time = time.time()
        while time.time() - start_time < MAX_WAIT_SECONDS:
            if is_site_reachable(TARGET_URL):
                window.load_url(TARGET_URL)
                return
            time.sleep(CHECK_INTERVAL_SECONDS)

        window.load_html(ERROR_HTML)
    except Exception:
        try:
            window.load_html(ERROR_HTML)
        except Exception:
            pass  # window itself may already be gone (user closed it) — nothing more to do


def _show_native_error(message):
    """Last-resort fallback if pywebview can't even create a window (most
    commonly: the Microsoft Edge WebView2 Runtime isn't installed). Uses
    only Python's built-in ctypes so it works even if webview itself is
    broken."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, "Creoveya", 0x10)  # MB_ICONERROR
    except Exception:
        print(message)


def main():
    try:
        api = Api()
        window = webview.create_window(
            APP_TITLE,
            html=SPLASH_HTML,
            width=1280,
            height=800,
            min_size=(960, 640),
            js_api=api,
        )
        api.window = window

        # connect_and_load runs in a background thread once the native
        # window is up, so the splash screen is visible immediately
        # instead of a blank/frozen window while we wait on the network.
        webview.start(connect_and_load, window, gui="edgechromium", debug=False)

    except Exception as exc:
        # Most common cause: the Microsoft Edge WebView2 Runtime isn't
        # installed on this machine (pywebview's Windows backend depends
        # on it). Recent Windows 10/11 ship with it by default, but older
        # or locked-down machines may not have it.
        _show_native_error(
            "Creoveya couldn't start.\n\n"
            "This usually means the Microsoft Edge WebView2 Runtime isn't "
            "installed on this PC. Please install it from:\n"
            "https://developer.microsoft.com/microsoft-edge/webview2/\n\n"
            f"Technical details: {exc}"
        )


if __name__ == "__main__":
    main()
