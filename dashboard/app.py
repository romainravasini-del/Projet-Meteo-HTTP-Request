import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import pandas as pd
import plotly.express as px

# 1. Configuration de la page
st.set_page_config("Observatoire Météo", layout="wide")
st.title("🌤️ Observatoire Météo - Dashboard")

API_URL = "http://127.0.0.1:8000"

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

def get_meteo_ville(ville: str):
    try:
        resp = requests.get(f"{API_URL}/meteo/{ville}", timeout=3)
        if resp.status_code == 200:
            return resp.json()
        return None
    except requests.exceptions.RequestException:
        return None

def get_historique_ville(ville: str):
    try:
        resp = requests.get(f"{API_URL}/meteo/{ville}/historique", timeout=3)
        if resp.status_code == 200:
            return resp.json()
        return None
    except requests.exceptions.RequestException:
        return None

# 2. Statistiques globales de l'observatoire
stats = get_status()

if stats:
    st.subheader("📊 Statistiques Globales de l'Observatoire")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Température Moyenne", f"{stats['temperature_moyenne']} °C")
    col2.metric("Température Min", f"{stats['temperature_min']} °C")
    col3.metric("Température Max", f"{stats['temperature_max']} °C")
    col4.metric("Vent Moyen", f"{stats['vent_moyen']} km/h")

st.divider()

# 3. Météo spécifique par ville (interactivité, métriques & graphiques Plotly)
st.subheader("📍 Météo en direct par Ville")

VILLES = [
    "Paris", "Marseille", "Lyon", "Toulouse", "Nice",
    "Nantes", "Strasbourg", "Bordeaux", "Lille", "Brest"
]

ville_selectionnee = st.selectbox("Sélectionnez une ville à observer :", options=VILLES)

if ville_selectionnee:
    meteo_data = get_meteo_ville(ville_selectionnee)
    if meteo_data and "releve" in meteo_data and meteo_data["releve"]:
        releve = meteo_data["releve"]
        m1, m2, m3 = st.columns(3)
        m1.metric("🌡️ Température Actuelle", f"{releve['temperature']} °C")
        m2.metric("💨 Vitesse du Vent", f"{releve['vitesse_vent']} km/h")
        m3.metric("🕒 Heure du Relevé", releve["date_heure"].replace("T", " à "))

        # Récupération et affichage des graphiques d'historique (Plotly)
        historique = get_historique_ville(ville_selectionnee)
        if historique and "releves" in historique and historique["releves"]:
            df = pd.DataFrame(historique["releves"])
            # Tri chronologique pour le tracé de la courbe
            df = df.sort_values("date_heure")

            tab_temp, tab_vent = st.tabs(["📈 Évolution Température", "💨 Évolution Vent"])

            with tab_temp:
                fig_temp = px.line(
                    df,
                    x="date_heure",
                    y="temperature",
                    title=f"Évolution de la Température à {ville_selectionnee} (°C)",
                    markers=True,
                    labels={"date_heure": "Date et Heure", "temperature": "Température (°C)"}
                )
                st.plotly_chart(fig_temp, use_container_width=True)

            with tab_vent:
                fig_vent = px.line(
                    df,
                    x="date_heure",
                    y="vitesse_vent",
                    title=f"Évolution du Vent à {ville_selectionnee} (km/h)",
                    markers=True,
                    labels={"date_heure": "Date et Heure", "vitesse_vent": "Vitesse du Vent (km/h)"}
                )
                st.plotly_chart(fig_vent, use_container_width=True)
    else:
        st.warning(f"Aucun relevé disponible pour {ville_selectionnee}.")

st.divider()

# 4. Carte interactive des villes observées (Folium)
st.subheader("🗺️ Carte des Villes Observées")

COORDONNEES = {
    "Paris": [48.8566, 2.3522],
    "Marseille": [43.2965, 5.3698],
    "Lyon": [45.7640, 4.8357],
    "Toulouse": [43.6047, 1.4442],
    "Nice": [43.7102, 7.2620],
    "Nantes": [47.2184, -1.5536],
    "Strasbourg": [48.5734, 7.7521],
    "Bordeaux": [44.8378, -0.5792],
    "Lille": [50.6292, 3.0573],
    "Brest": [48.3904, -4.4861],
}

carte = folium.Map(location=[46.6, 2.2], zoom_start=6)

for ville, coords in COORDONNEES.items():
    couleur = "red" if ville == ville_selectionnee else "blue"
    folium.Marker(
        location=coords,
        popup=ville,
        tooltip=ville,
        icon=folium.Icon(color=couleur, icon="cloud"),
    ).add_to(carte)

st_folium(carte, use_container_width=True, height=500)
