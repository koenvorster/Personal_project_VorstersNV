#!/usr/bin/env bash
# init_modellen.sh – Laadt de benodigde Ollama-modellen na het opstarten.
# Gebruik: bash scripts/init_modellen.sh

set -euo pipefail

OLLAMA_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
CHAT_MODEL="${OLLAMA_CHAT_MODEL:-llama3:8b}"
EMBED_MODEL="${OLLAMA_EMBED_MODEL:-nomic-embed-text}"

echo ">>> Wachten op Ollama ($OLLAMA_URL)…"
until curl -sf "$OLLAMA_URL/api/tags" > /dev/null; do
  sleep 3
done
echo ">>> Ollama is bereikbaar."

echo ">>> Chat-model laden: $CHAT_MODEL"
curl -sf -X POST "$OLLAMA_URL/api/pull" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"$CHAT_MODEL\"}" | tail -1

echo ">>> Embed-model laden: $EMBED_MODEL"
curl -sf -X POST "$OLLAMA_URL/api/pull" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"$EMBED_MODEL\"}" | tail -1

echo ">>> Klaar! Beschikbare modellen:"
curl -sf "$OLLAMA_URL/api/tags" | python3 -c \
  "import sys,json; [print(' •', m['name']) for m in json.load(sys.stdin)['models']]"
