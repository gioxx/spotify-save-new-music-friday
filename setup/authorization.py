import os
import base64
import requests
from dotenv import load_dotenv
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser

# Load the .env file
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8888/callback"  # You can change this, but it must be registered in the Spotify app
SCOPES = "playlist-modify-public playlist-modify-private"

if not CLIENT_ID or not CLIENT_SECRET:
    print("CLIENT_ID or CLIENT_SECRET not found in the .env file")
    exit(1)

# Authorization URL
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"

# Global variable for the authorization code
auth_code = None


class OAuthServerHandler(BaseHTTPRequestHandler):
    """Handler to capture the Spotify authorization code."""
    def do_GET(self):
        global auth_code
        if "/callback" in self.path:
            query = self.path.split("?")[1]
            params = {key: value for key, value in (p.split("=") for p in query.split("&"))}
            auth_code = params.get("code")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Authorization successful. You can close this window.")
        else:
            self.send_response(404)
            self.end_headers()


def start_server():
    """Start an HTTP server to capture the authorization code."""
    server = HTTPServer(("localhost", 8888), OAuthServerHandler)
    print("Server waiting for the authorization code...")
    server.handle_request()
    return auth_code


def get_authorization_code():
    """Get the authorization code by opening the browser."""
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
    }
    auth_request_url = f"{AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    webbrowser.open(auth_request_url)
    return start_server()


def get_refresh_token(auth_code):
    """Exchange the authorization code for an access token and a refresh token."""
    client_creds = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_creds = base64.b64encode(client_creds.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_creds}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
    }

    response = requests.post(TOKEN_URL, data=payload, headers=headers)
    if response.status_code == 200:
        token_data = response.json()
        print("Access Token:", token_data.get("access_token"))
        print("Refresh Token:", token_data.get("refresh_token"))
        return token_data.get("refresh_token")
    else:
        print("Error during the token exchange process.")
        print(response.status_code, response.reason)
        print(response.json())
        return None


if __name__ == "__main__":
    print("Step 1: Get the authorization code...")
    auth_code = get_authorization_code()

    if not auth_code:
        print("Error: Unable to get the authorization code.")
        exit(1)

    print("Step 2: Exchange the authorization code for a refresh token...")
    refresh_token = get_refresh_token(auth_code)

    if refresh_token:
        print("\nOperation completed!")
        print(f"Save your REFRESH_TOKEN in the .env file:\nREFRESH_TOKEN={refresh_token}")
    else:
        print("Error: Unable to get the refresh token.")
