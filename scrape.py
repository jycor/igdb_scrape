import os
import json
import time
import pickle
import requests

from dotenv import load_dotenv
load_dotenv()

LAST_GAME_ID = 321687 # as of 11/09/2024
BATCH_SIZE = 500

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

companyCache = {}
if os.path.exists("companies.pkl"):
    with open("companies.pkl", "rb") as f:
        companyCache = pickle.load(f)
        f.close()

def get_company(id):
    if id in companyCache:
        return
    query = COMPANY_QUERY.format(start=id, end=id + BATCH_SIZE, batch_size=BATCH_SIZE)
    print("COMPANY QUERY:", query)

    time.sleep(DELAY)
    response = requests.post(COMPANY_URL, headers=HEADERS, data=query)
    if response.status_code != 200:
        print("COMPANY QUERY FAILED WITH:", response.status_code)
        print(response.json())
        return
    for company in response.json():
        companyCache[company["id"]] = company["name"]

    with open("companies.pkl", "wb") as f:
        pickle.dump(companyCache, f)
        f.close()


INVOLVED_COMPANY_URL = "https://api.igdb.com/v4/involved_companies"
INVOLVED_COMPANY_QUERY = """
fields id, company, developer, publisher;
where id >= {start} & id < {end};
limit {batch_size};
"""

involvedCompanyCache = {}
if os.path.exists("involved_companies.pkl"):
    with open("involved_companies.pkl", "rb") as f:
        involvedCompanyCache = pickle.load(f)
        f.close()

def get_involved_company(id):
    if id in involvedCompanyCache:
        return
    query = INVOLVED_COMPANY_QUERY.format(start=id, end=id + BATCH_SIZE, batch_size=BATCH_SIZE)
    print("INVOLVED COMPANY QUERY:", query)

    response = requests.post(INVOLVED_COMPANY_URL, headers=HEADERS, data=query)
    if response.status_code != 200:
        print("COMPANY QUERY FAILED WITH:", response.status_code)
        print(response.json())
        return
    for company in response.json():
        involvedCompanyCache[company["id"]] = company
        get_company(company["company"])
    
    with open("involved_companies.pkl", "wb") as f:
        pickle.dump(involvedCompanyCache, f)
        f.close()


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
coverCache = set()
if os.path.exists("covers.pkl"):
    with open("covers.pkl", "rb") as f:
        coverCache = pickle.load(f)
        f.close()

def get_cover(id):
    if id in coverCache:
        return
    query = COVER_QUERY.format(start=id, end=id + BATCH_SIZE, batch_size=BATCH_SIZE)
    print("COVER QUERY:", query)

    time.sleep(DELAY)
    response = requests.post(COVER_URL, headers=HEADERS, data=query)
    if response.status_code != 200:
        print("COVER QUERY FAILED WITH:", response.status_code)
        print(response.json())
        return
    for cover in response.json():
        if cover["id"] in coverCache:
            continue
        coverCache.add(cover["id"])

        img_hash = cover["image_id"]
        img_url = COVER_DOWNLOAD_URL.format(img_hash)
        print("GETTING IMAGE:", img_url)
        img = requests.get(img_url) # TODO: rate limit?
        if img.status_code != 200:
            print("IMAGE QUERY FAILED WITH:", response.status_code)
            print(response.json())
            return
        with open("covers/{}.jpg".format(img_hash), "wb") as f:
            f.write(img.content)
            f.close()

    with open("covers.pkl", "wb") as f:
        pickle.dump(coverCache, f)
        f.close()

GAME_URL = "https://api.igdb.com/v4/games"
GAME_QUERY = """
fields id, name, first_release_date, involved_companies, platforms, genres, summary, cover; 
where id > {start_id} & id <= {end_id}; 
limit {batch_size};
"""

# TODO: testing
BATCH_SIZE = 3
LAST_GAME_ID = 10
all_games = []
def get_game_batch(start, end, batch_size=BATCH_SIZE):
    query = GAME_QUERY.format(start_id=start, end_id=end, batch_size=batch_size)
    print("GAME QUERY:", query)

    time.sleep(DELAY)
    response = requests.post(GAME_URL, headers=HEADERS, data=query)
    if response.status_code != 200:
        print("GAME QUERY FAILED WITH:", response.status_code)
        print(response.json())
        return
    games = response.json()
    all_games.extend(response.json())
    return games

# Get everything
for i in range(0, LAST_GAME_ID, BATCH_SIZE):
    batch = get_game_batch(i, i+BATCH_SIZE)
    for game in batch:
        get_cover(game["cover"])
        for company in game["involved_companies"]:
            get_involved_company(company)

# Export games
print("Exporting {} games".format(len(all_games)))
with open("games.json", "w") as f:
    sorted_games = sorted(all_games, key=lambda x: x["id"])
    json.dump(all_games, f, sort_keys=True)
    f.close()

# Export companies
with open("company.json", "w") as f:
    involvedCompanies = sorted(involvedCompanyCache.values(), key=lambda x: x["id"])
    for involvedCompany in involvedCompanies:
        involvedCompany["name"] = companyCache[involvedCompany["company"]]
    json.dump(involvedCompanies, f, sort_keys=True)
    f.close()