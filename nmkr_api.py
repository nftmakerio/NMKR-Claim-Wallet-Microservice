import requests
from config import BEARER_TOKEN

BASE_URL = 'https://studio-api.nmkr.io/v2/'

def mint_and_send_random(project_id, wallet_address):
    """Mint and send a random item from the project to a given wallet address."""
    
    url = f"{BASE_URL}MintAndSendRandom/{project_id}/1/{wallet_address}"
    headers = {
        'accept': 'text/plain',
        'Authorization': f'Bearer {BEARER_TOKEN}'
    }
    
    response = requests.get(url, headers=headers)
    
    # Ensure to handle the response as needed, for this example, we simply return the response.
    return response
