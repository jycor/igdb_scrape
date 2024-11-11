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
def get_genres():
    if os.path.exists("genres.json"):
        return
    print("GENRE QUERY:", GENRE_QUERY)

    time.sleep(DELAY)
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
# Load Cache
def get_platforms():
    if os.path.exists("platforms.json"):
        return
    print("PLATFORM QUERY:", PLATFORM_QUERY)

    time.sleep(DELAY)
    response = requests.post(PLATFORM_URL, headers=HEADERS, data=PLATFORM_QUERY)
    sorted_platforms = sorted(response.json(), key=lambda x: x["id"])
    with open("platforms.json", "w") as f:
        json.dump(sorted_platforms, f, sort_keys=True)
        f.close()

get_platforms()


COMPANY_URL = "https://api.igdb.com/v4/companies"
COMPANY_QUERY = """
fields id, name;
where id >= {start} & id < {end};
limit {batch_size};
"""

company_cache = {}
if os.path.exists("companies.pkl"):
    with open("companies.pkl", "rb") as f:
        company_cache = pickle.load(f)
        f.close()

def get_company(id):
    if id in company_cache:
        return 0
    query = COMPANY_QUERY.format(start=id, end=id + SEARCH_BATCH_SIZE, batch_size=SEARCH_BATCH_SIZE)
    print("COMPANY QUERY:", query)

    time.sleep(DELAY)
    response = requests.post(COMPANY_URL, headers=HEADERS, data=query)
    if response.status_code != 200:
        print("COMPANY QUERY FAILED WITH:", response.status_code)
        print(response.json())
        return 1
    for company in response.json():
        company_cache[company["id"]] = company["name"]

    with open("companies.pkl", "wb") as f:
        pickle.dump(company_cache, f)
        f.close()


INVOLVED_COMPANY_URL = "https://api.igdb.com/v4/involved_companies"
INVOLVED_COMPANY_QUERY = """
fields id, company, developer, publisher;
where id >= {start} & id < {end};
limit {batch_size};
"""

involved_company_cache = {}
if os.path.exists("involved_companies.pkl"):
    with open("involved_companies.pkl", "rb") as f:
        involved_company_cache = pickle.load(f)
        f.close()

def get_involved_company(id):
    if id in involved_company_cache:
        return 0
    query = INVOLVED_COMPANY_QUERY.format(start=id, end=id + SEARCH_BATCH_SIZE, batch_size=SEARCH_BATCH_SIZE)
    print("INVOLVED COMPANY QUERY:", query)

    time.sleep(DELAY)
    response = requests.post(INVOLVED_COMPANY_URL, headers=HEADERS, data=query)
    if response.status_code != 200:
        print("COMPANY QUERY FAILED WITH:", response.status_code)
        print(response.json())
        return 1
    for company in response.json():
        involved_company_cache[company["id"]] = company
        if "company" not in company:
            continue
        if get_company(company["company"]) == 1:
            return 1
    
    with open("involved_companies.pkl", "wb") as f:
        pickle.dump(involved_company_cache, f)
        f.close()
    return 0


COVER_URL = "https://api.igdb.com/v4/covers"
COVER_DOWNLOAD_URL = "https://images.igdb.com/igdb/image/upload/t_1080p/{}.jpg"
COVER_QUERY = """
fields id, image_id;
where id >= {start} & id < {end};
limit {batch_size};
"""

if not os.path.exists("covers"):
    os.makedirs("covers")

# Load Cache
cover_cache = {}
if os.path.exists("covers.pkl"):
    with open("covers.pkl", "rb") as f:
        cover_cache = pickle.load(f)
        f.close()

def get_cover(id):
    if id in cover_cache:
        return 0
    query = COVER_QUERY.format(start=id, end=id + SEARCH_BATCH_SIZE, batch_size=SEARCH_BATCH_SIZE)
    print("COVER QUERY:", query)

    time.sleep(DELAY)
    response = requests.post(COVER_URL, headers=HEADERS, data=query)
    if response.status_code != 200:
        print("COVER QUERY FAILED WITH:", response.status_code)
        print(response.json())
        return 1
    for cover in response.json():
        if cover["id"] in cover_cache:
            continue
        img_hash = cover["image_id"]
        img_url = COVER_DOWNLOAD_URL.format(img_hash)
        print("GETTING IMAGE:", img_url)
        img = requests.get(img_url) # TODO: rate limit?
        if img.status_code != 200:
            print("IMAGE QUERY FAILED WITH:", response.status_code)
            print(response.json())
            return 1
        with open("covers/{}.jpg".format(img_hash), "wb") as f:
            f.write(img.content)
            f.close()
        cover_cache[cover["id"]] = cover

    with open("covers.pkl", "wb") as f:
        pickle.dump(cover_cache, f)
        f.close()
    return 0

GAME_URL = "https://api.igdb.com/v4/games"
GAME_QUERY = """
fields id, name, first_release_date, involved_companies, platforms, genres, summary, cover; 
where id > {start_id} & id <= {end_id}; 
limit {batch_size};
"""

games_cache = []
last_id = 0
if os.path.exists("games.pkl"):
    with open("games.pkl", "rb") as f:
        games_cache = pickle.load(f)
        f.close()
    for game in games_cache:
        last_id = max(last_id, game["id"])
    print("RELOADED GAME, RESUMING FROM ID:", last_id)

def get_game_batch(start, end, batch_size=BATCH_SIZE):
    global last_id
    query = GAME_QUERY.format(start_id=start, end_id=end, batch_size=batch_size)
    print("GAME QUERY:", query)

    time.sleep(DELAY)
    response = requests.post(GAME_URL, headers=HEADERS, data=query)
    if response.status_code != 200:
        print("GAME QUERY FAILED WITH:", response.status_code)
        print(response.json())
        return None, 1
    
    return response.json(), 0

# Get everything
# for i in range(last_id, LAST_GAME_ID, BATCH_SIZE):
#     batch, ok = get_game_batch(i, i+BATCH_SIZE)
#     if ok == 1:
#         print("FAILED TO GET BATCH")
#         exit(1)
#     for game in batch:
#         if "cover" in game and get_cover(game["cover"]) == 1:
#             exit(1)
#         if "involved_companies" not in game:
#             continue
#         for company in game["involved_companies"]:
#             if get_involved_company(company) == 1:
#                 exit(1)
#     games_cache.extend(batch)
#     with open("games.pkl", "wb") as f:
#         pickle.dump(games_cache, f)
#         f.close()
#     last_id = max([game["id"] for game in batch])

# Export games
print("Exporting {} games".format(len(games_cache)))
with open("games.json", "w") as f:
    sorted_games = sorted(games_cache, key=lambda x: x["id"])
    json.dump(sorted_games, f, sort_keys=True)
    f.close()

# # Export covers
# with open("covers.json", "w") as f:
#     sorted_covers = sorted(cover_cache.values(), key=lambda x: x["id"])
#     json.dump(sorted_covers, f, sort_keys=True)
#     f.close()

# # Export companies
# with open("companies.json", "w") as f:
#     sorted_companies = sorted(involved_company_cache.values(), key=lambda x: x["id"])
#     for company in sorted_companies:
#         company["name"] = company_cache[company["company"]]
#     json.dump(sorted_companies, f, sort_keys=True)
#     f.close()
