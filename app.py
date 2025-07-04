import streamlit as st
import requests
import time
import base64
import json

# Wczytanie danych z .streamlit/secrets.toml
CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
WEBHOOK_URL = st.secrets["WEBHOOK_URL"]

# Inicjalizacja zmiennych sesji
for key in ["device_code", "polling_interval", "access_token", "refresh_token"]:
    if key not in st.session_state:
        st.session_state[key] = None

def send_token_via_webhook(access_token, refresh_token):
    try:
        headers = {'Content-Type': 'application/json'}
        data = {
            'access_token': access_token,
            'refresh_token': refresh_token
        }
        response = requests.post(WEBHOOK_URL, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        st.success("Tokeny zostały pomyślnie nadane!")
    except requests.exceptions.RequestException as e:
        st.error(f"Błąd wysyłania webhooka: {e}")

def get_token():
    auth_string = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    token_url = "https://allegro.pl/auth/oauth/token"
    headers = {
        "Authorization": f"Basic {auth_string}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    params = {
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "device_code": st.session_state['device_code']
    }

    response = requests.post(token_url, headers=headers, data=params)

    if response.status_code == 200:
        response_data = response.json()
        st.session_state['access_token'] = response_data.get('access_token')
        st.session_state['refresh_token'] = response_data.get('refresh_token')
        st.success("Pomyślnie autoryzowano!")
        send_token_via_webhook(st.session_state['access_token'], st.session_state['refresh_token'])
    else:
        error = response.json().get('error')
        if error == 'authorization_pending':
            st.info("Oczekiwanie na autoryzację w Allegro. Spróbuj ponownie za chwilę.")
        elif error == 'slow_down':
            st.warning("Zbyt częste zapytania. Odczekaj chwilę przed kolejnym sprawdzeniem.")
        else:
            st.error(f"Błąd podczas pobierania tokenu: {response.json()}")

# Stylowanie przycisku
st.markdown("""
<style>
div.stButton > button {
    font-size: 20px;
    padding: 15px 30px;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    transition: background-color 0.3s ease;
}
div.stButton > button:hover {
    background-color: #45a049;
}
</style>""", unsafe_allow_html=True)

# Inicjalizacja procesu autoryzacji
if st.button("Autoryzuj z Allegro") and not st.session_state['device_code']:
    auth_string = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    device_url = "https://allegro.pl/auth/oauth/device"
    headers = {
        "Authorization": f"Basic {auth_string}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "client_id": CLIENT_ID
    }
    device_response = requests.post(device_url, headers=headers, data=data)

    if device_response.status_code == 200:
        response_data = device_response.json()
        st.session_state['device_code'] = response_data.get('device_code')
        st.session_state['polling_interval'] = response_data.get('interval')

        verification_uri_complete = response_data.get('verification_uri_complete')
        user_code = response_data.get('user_code')

        st.success("Rozpoczęto autoryzację.")
        st.markdown(f"**1.** Przejdź do: [**{verification_uri_complete}**]({verification_uri_complete})")
        st.markdown(f"**2.** Wprowadź kod autoryzacyjny: **`{user_code}`**")
        st.info("Po autoryzacji wróć tutaj i kliknij 'Sprawdź status autoryzacji'.")
    else:
        st.error("Nie udało się zainicjować autoryzacji.")

# Przycisk do sprawdzenia statusu autoryzacji
if st.session_state['device_code'] and not st.session_state['access_token']:
    if st.button("Sprawdź status autoryzacji"):
        get_token()

# Komunikat końcowy
if st.session_state['access_token']:
    st.markdown("---")
    st.subheader("✅ Autoryzacja zakończona")
    st.info("Dostęp został przydzielony. Możesz teraz zamknąć tę stronę.")
