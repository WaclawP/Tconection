import streamlit as st
import requests
import time
import base64
import json

CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
WEBHOOK_URL = st.secrets["WEBHOOK_URL"]

# Initialize session state variables
if 'device_code' not in st.session_state:
    st.session_state['device_code'] = None
if 'polling_interval' not in st.session_state:
    st.session_state['polling_interval'] = None
if 'access_token' not in st.session_state:
    st.session_state['access_token'] = None
if 'refresh_token' not in st.session_state:
    st.session_state['refresh_token'] = None

def send_token_via_webhook(access_token, refresh_token):
    """Sends the access and refresh tokens to a predefined webhook URL."""
    try:
        headers = {'Content-Type': 'application/json'}
        data = {
            'access_token': access_token,
            'refresh_token': refresh_token
        }
        response = requests.post(WEBHOOK_URL, headers=headers, data=json.dumps(data))
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        st.success("Tokeny zostały pomyślnie nadane!")
    except requests.exceptions.RequestException as e:
        st.error(f"Błąd wysyłania webhooka: {e}")

def get_token():
    """Polls Allegro API for the access and refresh tokens using the device code."""
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
    elif response.json().get('error') == 'authorization_pending':
        st.info("Oczekiwanie na autoryzację w Allegro...")
    elif response.json().get('error') == 'slow_down':
        sleep_interval = st.session_state.get('polling_interval', 5)
        time.sleep(sleep_interval)
        get_token() # Re-call the function to continue polling
    else:
        st.error(f"Błąd podczas pobierania tokenu: {response.json()}")

---

# Obsługa ofert poprzez API

Here's how to achieve your desired changes:

```python
# Custom CSS for button styling
st.markdown("""
<style>
div.stButton > button {
    font-size: 20px; /* Adjust font size for bigger button */
    padding: 15px 30px; /* Adjust padding for bigger button */
    background-color: #4CAF50; /* Allegro-like green */
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

if st.button("Autoryzuj z Allegro", type="primary") and st.session_state['device_code'] is None:
    auth_string = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    device_url = "[https://allegro.pl/auth/oauth/device](https://allegro.pl/auth/oauth/device)"
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
        user_code = response_data.get('user_code')
        verification_uri_complete = response_data.get('verification_uri_complete')
        st.session_state['device_code'] = response_data.get('device_code')
        st.session_state['polling_interval'] = response_data.get('interval')

        st.markdown(f"Proszę odwiedzić: {verification_uri_complete}")
        st.info(f"Kod do wpisania (jeśli wymagany): **{user_code}**") # Display user_code more prominently

        # Start polling for tokens
        while st.session_state['access_token'] is None and st.session_state['device_code'] is not None:
            time.sleep(st.session_state.get('polling_interval', 5))
            get_token()
    else:
        st.error("Nie udało się zainicjować autoryzacji. Spróbuj ponownie.")

if st.session_state['access_token']:
    st.markdown("---")
    st.subheader("Tokens obtained successfully!")
    #st.write(f"**Access Token:** `{'*' * len(st.session_state['access_token'])}`") # Masked display
    #st.write(f"**Refresh Token:** `{'*' * len(st.session_state['refresh_token'])}`") # Masked display
    st.info("Dostęp został przydzielony. Możesz teraz zamknąć tę stronę.")
