import streamlit as st
import requests
import time
import base64
import json


CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
WEBHOOK_URL = st.secrets["WEBHOOK_URL"]

if 'device_code' not in st.session_state:
    st.session_state['device_code'] = None
if 'polling_interval' not in st.session_state:
    st.session_state['polling_interval'] = None
if 'access_token' not in st.session_state:
    st.session_state['access_token'] = None
konto = st.text_input("wpisz nazwę konta")
if len(konto) >=3 :
    def send_token_via_webhook(token):
        try:
            headers = {'Content-Type': 'application/json', 'konto': konto}
            data = {'access_token': token}
            response = requests.post(WEBHOOK_URL, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            st.success("Token nadany")
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
            st.session_state['access_token'] = response.json().get('access_token')
            st.success("Pomyślnie autoryzowano!")
            send_token_via_webhook(st.session_state['access_token'])
        elif response.json().get('error') == 'authorization_pending':
            st.info("Oczekiwanie na autoryzację...")
        elif response.json().get('error') == 'slow_down':
            time.sleep(st.session_state['polling_interval'])
            get_token()  # ponowne wywołanie funkcji
        else:
            st.error(f"Błąd podczas pobierania tokenu: {response.json()}")
        if st.button("Authorize with Allegro") and st.session_state['device_code'] is None:
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
                data = device_response.json()
                user_code = data.get('user_code')
                verification_uri_complete = data.get('verification_uri_complete')
                st.session_state['device_code'] = data.get('device_code')
                st.session_state['polling_interval'] = data.get('interval')
                st.markdown(f"Proszę odwiedzić: {verification_uri_complete}  ") #kod: {user_code} mozna dodac ale czesto jest
                while st.session_state['access_token'] is None and st.session_state['device_code'] is not None:
                    time.sleep(3)
                    get_token()
            else:
                st.error("Nie udało się zainicjować autoryzacji.")
        
        if st.session_state['access_token']:
            st.success(f"=================================================")
else:
    time.sleep(1)
