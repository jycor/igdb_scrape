import os
import json
import time
import pickle
import requests

from dotenv import load_dotenv
load_dotenv()

DELAY = 0.25 # 250ms to avoid rate limiting
BATCH_SIZE = 500

CLIENT_ID = os.getenv("CLIENT_ID")
AUTHORIZATION = os.getenv("AUTHORIZATION")
HEADERS = {
    "Client-ID": CLIENT_ID,
    "Authorization": "Bearer " + AUTHORIZATION,
}

# Get all cover ids from games.json
print("Loading cover ids from games.json...")
cover_ids = set()
games = json.load(open("games.json", "r"))
for game in games:
    if "cover" not in game:
        continue
    cover_ids.add(game["cover"])

print("Total unique covers:", len(cover_ids))
print("Estimated time {} seconds".format((len(cover_ids) * DELAY) / BATCH_SIZE))

# Sort the ids
sorted_cover_ids = sorted(list(cover_ids))


COVER_URL = "https://api.igdb.com/v4/covers"
COVER_DOWNLOAD_URL = "https://images.igdb.com/igdb/image/upload/t_1080p/{}.jpg"
COVER_BATCH_QUERY = """
fields id, image_id;
where id >= {start} & id < {end};
limit {batch_size};
"""

def load_cover_cache():
    if not os.path.exists("covers.pkl"):
        return []
    with open("covers.pkl", "rb") as f:
        return pickle.load(f)

print("Loading cover cache...")
cover_cache = load_cover_cache()
print("Loaded {} covers from cache...".format(len(cover_cache)))

# It turns out it's possible that the API is missing results as we query
for cover in cover_cache:
    cover_ids.discard(cover["id"])

def get_cover_batch(start, end, batch_size=BATCH_SIZE):
    query = COVER_BATCH_QUERY.format(start=start, end=end, batch_size=batch_size)
    # print("COVER QUERY:", query)

    time.sleep(DELAY)
    response = requests.post(COVER_URL, headers=HEADERS, data=query)
    if response.status_code != 200:
        print("COVER QUERY FAILED WITH:", response.status_code)
        print(response.json())
        return 1
    
    result = response.json()
    for cover in result:
        cover_ids.discard(cover["id"])
    
    cover_cache.extend(result)
    # print("Saving companies id {} to {}...".format(start, end))
    with open("covers.pkl", "wb") as f:
        pickle.dump(cover_cache, f)
    return 0

num_cover_ids = len(sorted_cover_ids)
for i in range(len(cover_cache), num_cover_ids, BATCH_SIZE):
    print("Getting batch {}/{}...".format(i/BATCH_SIZE, num_cover_ids/BATCH_SIZE))
    get_cover_batch(sorted_cover_ids[i], sorted_cover_ids[min(num_cover_ids - 1, i+BATCH_SIZE)])

if len(cover_ids) > 0:
    print("Missing {} covers".format(len(cover_ids)))
    print("Estimated time {} seconds".format(len(cover_ids) * DELAY))

COVER_QUERY = """
fields id, image_id;
where id = {id};
limit 1;
"""
def get_cover(id):
    query = COVER_QUERY.format(id=id)
    # print("COVER QUERY:", query)

    time.sleep(DELAY)
    response = requests.post(COVER_URL, headers=HEADERS, data=query)
    if response.status_code != 200:
        print("COVER QUERY FAILED WITH:", response.status_code)
        print(response.json())
        return 1
    
    # must have exactly 1 result
    result = response.json()
    if len(result) == 0:
        print("ID {} NOT FOUND".format(id))
        return 1
    
    cover_cache.extend(result)
    # print("Saving cover id {} to {}...".format(start, end))
    with open("covers.pkl", "wb") as f:
        pickle.dump(cover_cache, f)
    return 0

# TODO: it is much more efficient to batch these up again, but harder to determine if some are just missing
for missing_id in cover_ids:
    get_cover(missing_id)

# Export covers
print("Exporting {} covers...".format(len(cover_cache)))
with open("covers.json", "w") as f:
    sorted_covers = sorted(cover_cache, key=lambda x: x["id"])
    json.dump(sorted_covers, f, sort_keys=True)
    f.close()
