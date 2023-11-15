import pyotp
import requests
from config import twofa_pw, nmkr_api_secret

def generate_2fa_code():
    totp = pyotp.TOTP(twofa_pw)
    return totp.now()

def fetch_new_access_token():
    two_fa_code = generate_2fa_code()
    url = f"https://studio-api.nmkr.io/getaccesstoken/{nmkr_api_secret}/{two_fa_code}"
    
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('accessToken')
    else:
        raise Exception("Failed to fetch access token")
