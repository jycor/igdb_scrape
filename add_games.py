import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


file = open("games.json", "r")

content = file.read()

file.close()

data = json.loads(content)

for item in data:
    response = (supabase.table("games").insert(item).execute())
