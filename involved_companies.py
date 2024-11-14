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

# Get all involved company ids from games.json
print("Loading involved company ids from games.json...")
involved_company_ids = set()
games = json.load(open("games.json", "r"))
for game in games:
    if "involved_companies" not in game:
        continue
    for involved_company in game["involved_companies"]:
        involved_company_ids.add(involved_company)

print("Total unique involved companies:", len(involved_company_ids))
print("Estimated time {} seconds".format((len(involved_company_ids) * DELAY) / BATCH_SIZE))

# Sort the ids
involved_company_ids_list = sorted(list(involved_company_ids))

INVOLVED_COMPANY_URL = "https://api.igdb.com/v4/involved_companies"
INVOLVED_COMPANY_BATCH_QUERY = """
fields id, company, developer, publisher;
where id >= {start} & id < {end};
limit {batch_size};
"""
def load_involved_company_cache():
    if not os.path.exists("involved_companies.pkl"):
        return []
    with open("involved_companies.pkl", "rb") as f:
        return pickle.load(f)

print("Loading involved company cache...")
involved_company_cache = load_involved_company_cache()
print("Loaded {} involved companies from cache...".format(len(involved_company_cache)))

# It turns out it's possible that the API is missing results as we query
found_ids = set()
for involved_company in involved_company_cache:
    found_ids.add(involved_company["id"])

def get_involved_company_batch(start, end, batch_size=BATCH_SIZE):    
    query = INVOLVED_COMPANY_BATCH_QUERY.format(start=start, end=end, batch_size=batch_size)
    # print("INVOLVED COMPANY BATCH QUERY:", query)

    time.sleep(DELAY)
    response = requests.post(INVOLVED_COMPANY_URL, headers=HEADERS, data=query)
    if response.status_code != 200:
        print("INVOLVED COMPANY BATCH QUERY FAILED WITH:", response.status_code)
        print(response.json())
        return 1
    
    result = response.json()
    for involved_company in result:
        found_ids.add(involved_company["id"])

    involved_company_cache.extend(result)
    print("Saving involved companies id {} to {}...".format(start, end))
    with open("involved_companies.pkl", "wb") as f:
        pickle.dump(involved_company_cache, f)
    return 0

num_involved_company_ids = len(involved_company_ids_list)
for i in range(len(involved_company_cache), num_involved_company_ids, BATCH_SIZE):
    print("Getting batch {}/{}...".format(i/BATCH_SIZE, num_involved_company_ids/BATCH_SIZE))
    get_involved_company_batch(involved_company_ids_list[i], involved_company_ids_list[min(num_involved_company_ids - 1, i+BATCH_SIZE)])

missing_ids = involved_company_ids - found_ids
if len(missing_ids) > 0:
    print("Missing {} companies".format(len(missing_ids)))
    print("Estimated time {} seconds".format(len(missing_ids) * DELAY))

INVOLVED_COMPANY_QUERY = """
fields id, company, developer, publisher;
where id = {id};
limit 1;
"""
def get_involved_company(id):
    query = INVOLVED_COMPANY_QUERY.format(id=id)
    # print("INVOLVED COMPANY QUERY:", query)

    time.sleep(DELAY)
    response = requests.post(INVOLVED_COMPANY_URL, headers=HEADERS, data=query)
    if response.status_code != 200:
        print("INVOLVED COMPANY QUERY FAILED WITH:", response.status_code)
        print(response.json())
        return 1
    
    # must have exactly 1 result
    result = response.json()
    if len(result) == 0:
        print("ID {} NOT FOUND".format(id))
        return 1
    
    involved_company_cache.extend(result)
    # print("Saving involved companies id {}...".format(id))
    with open("involved_companies.pkl", "wb") as f:
        pickle.dump(involved_company_cache, f)
    return 0

for missing_id in missing_ids:
    get_involved_company(missing_id)

# Export involved companies
print("Exporting {} involved companies...".format(len(involved_company_cache)))
with open("involved_companies.json", "w") as f:
    sorted_companies = sorted(involved_company_cache, key=lambda x: x["id"])
    json.dump(sorted_companies, f, sort_keys=True)
