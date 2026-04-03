import streamlit as st
from api_client import haal_status_op


def render_status_pagina():
    st.header("🔍 Systeemstatus")
    st.caption("Controleer de bereikbaarheid van alle backend-componenten.")

    if st.button("🔄 Vernieuwen"):
        st.rerun()

    try:
        status = haal_status_op()

        # Algemene status
        alles_ok = status["ollama_bereikbaar"] and status["chroma_bereikbaar"]
        st.success("✅ Systeem gezond") if alles_ok else st.warning("⚠️ Gedeeltelijk beschikbaar")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🦙 Ollama")
            if status["ollama_bereikbaar"]:
                st.success("Bereikbaar")
                modellen = status.get("modellen_beschikbaar", [])
                if modellen:
                    st.write("**Beschikbare modellen:**")
                    for model in modellen:
                        st.write(f"• `{model}`")
                else:
                    st.info("Geen modellen geladen. Voer uit: `ollama pull llama3:8b`")
            else:
                st.error("Niet bereikbaar")
                st.code("docker compose up ollama", language="bash")

        with col2:
            st.subheader("🗄️ ChromaDB")
            if status["chroma_bereikbaar"]:
                st.success("Bereikbaar")
            else:
                st.error("Niet bereikbaar")
                st.code("docker compose up chromadb", language="bash")

        # Configuratietips
        with st.expander("💡 Opstarttips"):
            st.markdown("""
**Modellen installeren via Ollama:**
```bash
# Chat-model (aanbevolen voor zakelijk gebruik)
docker exec -it vorstersNV-ollama ollama pull llama3:8b

# Embed-model (verplicht voor RAG/zoekfunctionaliteit)
docker exec -it vorstersNV-ollama ollama pull nomic-embed-text

# Alternatief: kleiner maar snel model
docker exec -it vorstersNV-ollama ollama pull mistral:7b
```

**Hardware-tips:**
- 🟢 **GPU (NVIDIA)**: Zorg dat `NVIDIA Container Toolkit` geïnstalleerd is voor maximale snelheid.
- 🟡 **CPU-only**: Ollama werkt ook op CPU; verwacht langere responstijden (~30–60s per vraag).
- 💾 **RAM**: Minimaal 16 GB aanbevolen voor `llama3:8b`.
""")

    except Exception as exc:
        st.error(f"Backend niet bereikbaar: {exc}")
        st.info("Zorg dat de backend draait: `docker compose up`")
