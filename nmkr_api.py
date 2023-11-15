import requests
from twofa_code_generator import fetch_new_access_token
from datetime import datetime, timedelta

BASE_URL = 'https://studio-api.nmkr.io/v2/'

refresh_interval = timedelta(minutes=10)  # Refresh every 10 minutes
current_token = None
last_refresh_time = None

def mint_and_send_random(project_id, wallet_address):
    global last_refresh_time, current_token

    # Check if it's time to refresh the token
    if last_refresh_time == None:
        current_token = fetch_new_access_token()
        last_refresh_time = datetime.now()

    if datetime.now() >= last_refresh_time + refresh_interval:
        current_token = fetch_new_access_token()
        last_refresh_time = datetime.now()

    """Mint and send a random item from the project to a given wallet address."""
    
    url = f"{BASE_URL}MintAndSendRandom/{project_id}/1/{wallet_address}"
    headers = {
        'accept': 'text/plain',
        'Authorization': f'Bearer {current_token}'
    }
    
    response = requests.get(url, headers=headers)
    
    # Ensure to handle the response as needed, for this example, we simply return the response.
    return response
