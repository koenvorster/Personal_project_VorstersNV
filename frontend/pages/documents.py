import streamlit as st
from api_client import upload_documenten, haal_statistieken_op, verwijder_document


def render_documenten_pagina():
    st.header("📄 Documentbeheer")
    st.caption("Upload bedrijfsdocumenten om ze beschikbaar te maken voor de AI-assistent.")

    col_upload, col_stats = st.columns([2, 1])

    with col_upload:
        st.subheader("📤 Documenten uploaden")
        geupload = st.file_uploader(
            "Selecteer bestanden (PDF, TXT, DOCX, CSV)",
            type=["pdf", "txt", "docx", "csv"],
            accept_multiple_files=True,
            help="Maximaal 50 MB per bestand.",
        )

        if geupload and st.button("📥 Verwerken en opslaan", type="primary"):
            with st.spinner(f"{len(geupload)} bestand(en) verwerken…"):
                try:
                    resultaat = upload_documenten(geupload)
                    st.success(resultaat["bericht"])
                    for doc in resultaat["documenten"]:
                        icoon = "✅" if not doc["status"].startswith("fout") else "❌"
                        st.write(
                            f"{icoon} **{doc['bestandsnaam']}** — "
                            f"{doc['aantal_chunks']} chunks — {doc['status']}"
                        )
                    st.rerun()
                except Exception as exc:
                    st.error(f"Upload mislukt: {exc}")

    with col_stats:
        st.subheader("📊 Vector store")
        try:
            stats = haal_statistieken_op()
            st.metric("Totaal chunks", stats["aantal_documenten"])
            st.metric("Unieke bronnen", len(stats["unieke_bronnen"]))
        except Exception as exc:
            st.warning(f"Statistieken niet beschikbaar: {exc}")

    # Documentoverzicht + verwijderen
    st.divider()
    st.subheader("🗂️ Opgeslagen documenten")
    try:
        stats = haal_statistieken_op()
        bronnen = stats.get("unieke_bronnen", [])
        if not bronnen:
            st.info("Geen documenten opgeslagen. Upload hierboven bestanden.")
        else:
            for bron in bronnen:
                col_naam, col_knop = st.columns([4, 1])
                col_naam.write(f"📄 {bron}")
                if col_knop.button("🗑️", key=f"verwijder_{bron}", help=f"Verwijder {bron}"):
                    try:
                        res = verwijder_document(bron)
                        st.success(res["bericht"])
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Verwijderen mislukt: {exc}")
    except Exception as exc:
        st.warning(f"Documenten niet beschikbaar: {exc}")
