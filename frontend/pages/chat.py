import streamlit as st
from api_client import stuur_chat_vraag
from config import API_BASE_URL


def render_chat_pagina():
    st.header("💬 Chat met uw bedrijfsdocumenten")
    st.caption(
        "Stel vragen over uw geüploade documenten. "
        "De AI-assistent zoekt de relevante passages op en geeft een antwoord."
    )

    # Instellingen in de zijbalk
    with st.sidebar:
        st.subheader("⚙️ Instellingen")
        gebruik_docs = st.toggle(
            "Gebruik bedrijfsdocumenten (RAG)",
            value=True,
            help="Aan: de assistent zoekt in uw documenten. "
                 "Uit: directe LLM-aanroep zonder context.",
        )
        model_keuze = st.text_input(
            "Model (optioneel)",
            placeholder="bijv. llama3:8b of mistral:7b",
            help="Laat leeg om het standaard model te gebruiken.",
        )
        if st.button("🗑️ Gesprek wissen"):
            st.session_state.berichten = []
            st.rerun()

    # Chatgeschiedenis initialiseren
    if "berichten" not in st.session_state:
        st.session_state.berichten = []

    # Bestaande berichten weergeven
    for bericht in st.session_state.berichten:
        with st.chat_message(bericht["rol"]):
            st.markdown(bericht["inhoud"])
            if bericht.get("bronnen"):
                with st.expander("📚 Bronnen"):
                    for bron in bericht["bronnen"]:
                        st.write(f"• {bron}")

    # Invoerveld
    if vraag := st.chat_input("Stel uw vraag…"):
        # Gebruikersbericht toevoegen
        st.session_state.berichten.append({"rol": "user", "inhoud": vraag})
        with st.chat_message("user"):
            st.markdown(vraag)

        # Antwoord ophalen
        with st.chat_message("assistant"):
            with st.spinner("Antwoord genereren…"):
                try:
                    resultaat = stuur_chat_vraag(
                        vraag=vraag,
                        gebruik_documenten=gebruik_docs,
                        model=model_keuze or None,
                    )
                    antwoord = resultaat["antwoord"]
                    bronnen = resultaat.get("bronnen", [])
                    model_naam = resultaat.get("model_gebruikt", "onbekend")

                    st.markdown(antwoord)
                    st.caption(f"🤖 Model: `{model_naam}`")

                    if bronnen:
                        with st.expander("📚 Bronnen"):
                            for bron in bronnen:
                                st.write(f"• {bron}")

                    st.session_state.berichten.append({
                        "rol": "assistant",
                        "inhoud": antwoord,
                        "bronnen": bronnen,
                    })

                except Exception as exc:
                    fout_bericht = f"❌ Fout: {exc}"
                    st.error(fout_bericht)
                    st.session_state.berichten.append({
                        "rol": "assistant",
                        "inhoud": fout_bericht,
                        "bronnen": [],
                    })
