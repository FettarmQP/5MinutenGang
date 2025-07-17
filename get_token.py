import requests
import urllib.parse

def get_twitch_token():
    """
    Helper script to get Twitch OAuth token
    """
    
    # Deine App Credentials
    CLIENT_ID = "DEINE_CLIENT_ID_HIER"
    CLIENT_SECRET = "DEIN_CLIENT_SECRET_HIER"  # Von der Twitch Console
    REDIRECT_URI = "http://localhost:3000"
    
    # Schritt 1: Authorization URL generieren
    auth_url = (
        f"https://id.twitch.tv/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&response_type=code"
        f"&scope=chat:read+user:read:email"
    )
    
    print("1. Öffne diese URL in deinem Browser:")
    print(auth_url)
    print()
    print("2. Logge dich ein und autorisiere die App")
    print("3. Du wirst zu localhost:3000 weitergeleitet")
    print("4. Kopiere den 'code' Parameter aus der URL")
    print()
    
    # Schritt 2: Code eingeben
    auth_code = input("Gib den Authorization Code ein: ")
    
    # Schritt 3: Token austauschen
    token_url = "https://id.twitch.tv/oauth2/token"
    token_data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI
    }
    
    response = requests.post(token_url, data=token_data)
    
    if response.status_code == 200:
        token_info = response.json()
        print("\n✅ Token erfolgreich generiert!")
        print(f"Access Token: {token_info['access_token']}")
        print(f"Refresh Token: {token_info['refresh_token']}")
        print(f"Expires in: {token_info['expires_in']} Sekunden")
        
        # .env Datei erstellen
        with open('.env', 'w') as f:
            f.write(f"TWITCH_CLIENT_ID={CLIENT_ID}\n")
            f.write(f"TWITCH_ACCESS_TOKEN={token_info['access_token']}\n")
            f.write(f"TWITCH_CHANNEL=dein_kanal_name\n")
            f.write(f"SECRET_KEY=your-secret-key-here\n")
        
        print("\n📝 .env Datei wurde erstellt!")
        
    else:
        print(f"❌ Fehler: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    get_twitch_token()
