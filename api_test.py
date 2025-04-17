import requests
import os

# Load Pterodactyl API key from environment variable
PTERODACTYL_API_KEY = "ptlc_5PnNE8GTbr4Aw0bH25HizKuMRmWiuZjxNRhkA0gXTjz" #os.getenv("PTERODACTYL_API_KEY")
PTERODACTYL_URL = "https://Pterodactyl.local.McQueenLab.net/api"

HEADERS = {
    "Authorization": f"Bearer {PTERODACTYL_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def test_api_key():
    """Test if the Pterodactyl API key is valid by fetching user details."""
    url = f"{PTERODACTYL_URL}/client/account"
    
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            print("✅ API Key is valid!")
            print("Response:", response.json())
        elif response.status_code == 403:
            print("❌ API Key is invalid or lacks permissions!")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
            print(response.text)
    except requests.RequestException as e:
        print("❌ Failed to reach Pterodactyl API:", e)

test_api_key()
