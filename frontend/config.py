import os

# Backend API URL – kan worden overschreven via omgevingsvariabele
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

PAGINA_CHAT = "💬 Chat"
PAGINA_DOCUMENTEN = "📄 Documenten"
PAGINA_STATUS = "🔍 Systeemstatus"

APP_TITEL = "VorstersNV AI Assistent"
APP_ICOON = "🏢"
