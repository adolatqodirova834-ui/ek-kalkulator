"""EK kalkulyatori — Streamlit entry point.  Run: streamlit run app.py"""

import streamlit as st

from ui.sidebar import init_state, render_sidebar

st.set_page_config(page_title="EK kalkulyatori", page_icon="⚡", layout="wide")

init_state()
page = st.navigation([
    st.Page("views/kalkulyator.py", title="Asosiy kalkulyator", icon="🧮", default=True),
    st.Page("views/kinetika.py", title="Kinetika", icon="📈"),
])
render_sidebar()
page.run()
