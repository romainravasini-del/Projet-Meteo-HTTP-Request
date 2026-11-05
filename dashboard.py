import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config("Observatoire Météo", layout="wide")
st.title("🌤️ Observatoire Météo - Dashboard")

def get_status():
    try:
        resp = requests.get(f"{API_URL}/", timeout=3)
        if resp.status_code == 200:
            st.success("Connecté à l'API Météo")
            return resp.json()
        else:
            st.error("L'API a répondu avec une erreur")
            return None
    except requests.exceptions.RequestException:
        st.error("❌ Impossible de joindre l'API FastAPI sur le port 8000.")
        return None

stats = get_status()
