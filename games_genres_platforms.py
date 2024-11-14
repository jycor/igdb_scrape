import os
import json
import time
import pickle
import requests

from dotenv import load_dotenv
load_dotenv()

LAST_GAME_ID = 321687 # as of 11/09/2024
BATCH_SIZE = 500
SEARCH_BATCH_SIZE = 10

CLIENT_ID = os.getenv("CLIENT_ID")
AUTHORIZATION = os.getenv("AUTHORIZATION")
HEADERS = {
    "Client-ID": CLIENT_ID,
    "Authorization": "Bearer " + AUTHORIZATION,
}

# TODO: should implement some sort of multi-threading to speed up the process
DELAY = 0.25 # 250ms to avoid rate limiting

# There are only a few genres, so we can just get them all
GENRE_URL = "https://api.igdb.com/v4/genres"
GENRE_QUERY = """
fields id, name;
limit 500;
"""
def get_genres(overwrite=False):
    if os.path.exists("genres.json") and not overwrite:
        return
    
    time.sleep(DELAY)
    print("GENRE QUERY:", GENRE_QUERY)
    response = requests.post(GENRE_URL, headers=HEADERS, data=GENRE_QUERY)
    sorted_genres = sorted(response.json(), key=lambda x: x["id"])
    with open("genres.json", "w") as f:
        json.dump(sorted_genres, f, sort_keys=True)
        f.close()

get_genres()


# This grabs all ids less than or equal to provided id to reduce number of requests
PLATFORM_URL = "https://api.igdb.com/v4/platforms"
PLATFORM_QUERY = """
fields id, name;
limit 500;
"""
def get_platforms(overwrite=False):
    if os.path.exists("platforms.json") and not overwrite:
        return
    
    time.sleep(DELAY)
    print("PLATFORM QUERY:", PLATFORM_QUERY)
    response = requests.post(PLATFORM_URL, headers=HEADERS, data=PLATFORM_QUERY)
    sorted_platforms = sorted(response.json(), key=lambda x: x["id"])
    with open("platforms.json", "w") as f:
        json.dump(sorted_platforms, f, sort_keys=True)
        f.close()

get_platforms(overwrite=False)

# Load Cache
def load_game_cache():
    if not os.path.exists("games.pkl"):
        return []
    with open("games.pkl", "rb") as f:
        return pickle.load(f)
    
games_cache = load_game_cache()
last_id = max([game["id"] for game in games_cache], default=0)

GAME_URL = "https://api.igdb.com/v4/games"
GAME_QUERY = """
fields id, name, first_release_date, involved_companies, platforms, genres, summary, cover; 
where id > {start_id} & id <= {end_id}; 
limit {batch_size};
"""
def get_game_batch(start, end, batch_size=BATCH_SIZE):
    query = GAME_QUERY.format(start_id=start, end_id=end, batch_size=batch_size)

    time.sleep(DELAY)
    response = requests.post(GAME_URL, headers=HEADERS, data=query)
    if response.status_code != 200:
        print("GAME QUERY FAILED WITH:", response.status_code)
        print(response.json())
        return 1
    
    batch = response.json()
    games_cache.extend(batch)

    global last_id
    last_id = max([game["id"] for game in batch])
    with open("games.pkl", "wb") as f:
        pickle.dump(games_cache, f)

    return 0

def get_all_games(overwrite=False):
    global games_cache
    global last_id
    if overwrite:
        games_cache = []
        last_id = 0
    for i in range(last_id, LAST_GAME_ID, BATCH_SIZE):
        if get_game_batch(i, i+BATCH_SIZE) == 1:
            exit(1)

get_all_games(overwrite=False)

# Export games
print("Exporting {} games".format(len(games_cache)))
with open("games.json", "w") as f:
    sorted_games = sorted(games_cache, key=lambda x: x["id"])
    json.dump(sorted_games, f, sort_keys=True)
    f.close()
