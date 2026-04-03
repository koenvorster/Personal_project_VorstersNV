import streamlit as st
from config import APP_TITEL, APP_ICOON, PAGINA_CHAT, PAGINA_DOCUMENTEN, PAGINA_STATUS
from pages.chat import render_chat_pagina
from pages.documents import render_documenten_pagina
from pages.status import render_status_pagina

st.set_page_config(
    page_title=APP_TITEL,
    page_icon=APP_ICOON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Navigatie
with st.sidebar:
    st.title(f"{APP_ICOON} {APP_TITEL}")
    st.caption("Lokale AI — uw data blijft bij u")
    st.divider()
    pagina = st.radio(
        "Navigatie",
        [PAGINA_CHAT, PAGINA_DOCUMENTEN, PAGINA_STATUS],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("🔒 Alle verwerking gebeurt lokaal.\nGeen data naar externe servers.")

# Pagina renderen
if pagina == PAGINA_CHAT:
    render_chat_pagina()
elif pagina == PAGINA_DOCUMENTEN:
    render_documenten_pagina()
elif pagina == PAGINA_STATUS:
    render_status_pagina()
