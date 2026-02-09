import hashlib
import json
import os
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlencode, parse_qs, parse_qsl
import requests

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
]
HOST="localhost"
PORT=8080

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.server: "Server"
        if "?" in self.path:
            self.server.query_params = dict(parse_qsl(self.path.split("?")[1]))
        self.wfile.write(b"<h1>Hello, World!</h1>")

class Server(HTTPServer):
    def __init__(self, host: str, port: int):
        super().__init__((host, port), RequestHandler)
        self.query_params = {}
        


def authorize(secrets: dict[str, str]) -> dict[str, str]:
    redirect_uri = f"{secrets["redirect_uris"][0]}:{PORT}"

    params = {
        "response_type": "code", # authorization code from resource owner
        "client_id": secrets["client_id"],
        "redirect_uri": redirect_uri,
        "scope": " ".join(SCOPES),
        "state": hashlib.sha256(os.urandom(1024)).hexdigest(), # string to prevent CSRF
        "access_type": "offline", # get refresh token
    }
    url = f"{secrets["auth_uri"]}?{urlencode(params)}"
    if not webbrowser.open(url):
        raise RuntimeError("Failed to open browser")
    server = Server(HOST, PORT)
    try:
        server.handle_request()
    finally:
        server.server_close()

    if params["state"] != server.query_params.get("state"):
        raise RuntimeError("State mismatch")

    code = server.query_params["code"]

    # fetch access token
    params = {
        "grant_type": "authorization_code",
        "client_id": secrets["client_id"],
        "client_secret": secrets["client_secret"],
        "code": code,
        "redirect_uri": redirect_uri,
    }
    response = requests.post(secrets["token_uri"], data=params, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch access token: {response.status_code} {response.text}")
    return response.json()

def check_access_token(access_token: str) -> dict[str, str]:
    response = requests.post(f"https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={access_token}")
    if response.status_code != 200:
        raise RuntimeError(f"Failed to check access token: {response.status_code} {response.text}")
    return response.json()

def refresh_access_token(secrets: dict[str, str], refresh_token: str) -> dict[str, str]:
    params = {
        "grant_type": "refresh_token",
        "client_id": secrets["client_id"],
        "client_secret": secrets["client_secret"],
        "refresh_token": refresh_token,
    }
    response = requests.post(secrets["token_uri"], data=params, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if response.status_code != 200:
        raise RuntimeError(f"Failed to refresh access token: {response.status_code} {response.text}")
    return response.json()

if __name__ == "__main__":
    secrets = json.loads(Path("secret.json").read_text())["web"]

    print("\nAuthorized Token:")
    tokens = authorize(secrets)
    print(tokens)

    print("\nChecked Token:")
    token_info = check_access_token(tokens["access_token"])
    print(token_info)

    print("\nRefreshed Token:")
    refreshed_tokens = refresh_access_token(secrets, tokens["refresh_token"])
    print(refreshed_tokens)