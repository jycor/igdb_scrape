import os
from dotenv import load_dotenv
import requests

load_dotenv()
client_id = os.getenv("CLIENT_ID")
secret = os.getenv("SECRET")

auth_url = "https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={secret}&grant_type=client_credentials"
auth_response = requests.post(auth_url.format(client_id=client_id, secret=secret))
if auth_response.status_code != 200:
    print("Failed to authenticate")
    print(auth_response.json())
    exit(1)

print("Authentication successful")
print("Writing authorization to .env file")
with open(".env", "w") as f:
    token = auth_response.json()["access_token"]
    f.write('CLIENT_ID="{}"\n'.format(client_id))
    f.write('SECRET="{}"\n'.format(secret))
    f.write('AUTHORIZATION="{}"\n'.format(token))
