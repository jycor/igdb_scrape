import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def upload_games():
    f = open("games.json", "r")
    data = json.load(f)
    for i in range(0, len(data), 1000):
        print("Upserting games from {} to {}...".format(i, i+1000))
        supabase.table("games").upsert(data[i:i+1000]).execute()


def upload_companies():
    f = open("companies.json", "r")
    data = json.load(f)
    for i in range(0, len(data), 1000):
        print("Upserting companies from {} to {}...".format(i, i+1000))
        supabase.table("companies").upsert(data[i:i+1000]).execute()


def upload_covers():
    f = open("covers.json", "r")
    data = json.load(f)
    for i in range(0, len(data), 1000):
        print("Upserting covers from {} to {}...".format(i, i+1000))
        supabase.table("covers").upsert(data[i:i+1000]).execute()


def upload_genres():
    f = open("genres.json", "r")
    data = json.load(f)
    for i in range(0, len(data), 1000):
        print("Upserting genres from {} to {}...".format(i, i+1000))
        supabase.table("genres").upsert(data[i:i+1000]).execute()


def upload_platforms():
    f = open("platforms.json", "r")
    data = json.load(f)
    for i in range(0, len(data), 1000):
        print("Upserting platforms from {} to {}...".format(i, i+1000))
        supabase.table("platforms").upsert(data[i:i+1000]).execute()

    
# upload_games()
# upload_companies()
# upload_covers()
# upload_genres()
# upload_platforms()