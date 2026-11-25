"""
Configuration and Constants for Google Play Games Services (GPGS) API
"""

# Google Play Services OAuth endpoints
AUTH_URL = "https://android.clients.google.com/auth"
GAMES_API_BASE = "https://games.googleapis.com/games/v1"

# Scopes
SCOPE_GAMES = "https://www.googleapis.com/auth/games"
SCOPE_GAMES_LITE = "https://www.googleapis.com/auth/games_lite"

# Standard Google Play Games package and signing signature
PLAY_GAMES_PACKAGE = "com.google.android.play.games"
GOOGLE_CLIENT_SIG = "38918a453d07199354f8b19af05ec6562ced5788"

# User-Agent simulation (simulates modern Google Play Games app on Android)
USER_AGENT = "PlayGames/2026.01.50000 (Linux; U; Android 14; en_US; Pixel 8 Pro; Build/UQ1A.240205.004)"
