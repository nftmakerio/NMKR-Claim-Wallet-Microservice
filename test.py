import requests
from config import BEARER_TOKEN, nmkr_studio_user_id   

def check_if_wallet_exists(wallet_name):
    headers = {'Authorization': 'Bearer ' + BEARER_TOKEN}
    url = f'https://studio-api.nmkr.io/v2/ListAllWallets/{nmkr_studio_user_id}'
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        wallets = response.json()
        for wallet in wallets:
            if wallet.get('walletName', '').lower() == wallet_name.lower():
                return wallet.get('address')
    return False

# Example usage
wallet_name = 'patteqrick@nmkr.io'
wallet_address = check_if_wallet_exists(wallet_name)
print(wallet_address)
