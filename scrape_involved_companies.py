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
print("This should take about {} seconds...".format((len(involved_company_ids) * DELAY) / BATCH_SIZE))

# Sort the ids
involved_company_ids = sorted(list(involved_company_ids))

# TODO: should implement some sort of multi-threading to speed up the process

INVOLVED_COMPANY_URL = "https://api.igdb.com/v4/involved_companies"
INVOLVED_COMPANY_QUERY = """
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

def get_involved_company(start, end, batch_size=BATCH_SIZE):    
    query = INVOLVED_COMPANY_QUERY.format(start=start, end=end, batch_size=batch_size)
    print("INVOLVED COMPANY QUERY:", query)

    time.sleep(DELAY)
    response = requests.post(INVOLVED_COMPANY_URL, headers=HEADERS, data=query)
    if response.status_code != 200:
        print("INVOLVED COMPANY QUERY FAILED WITH:", response.status_code)
        print(response.json())
        return 1
    
    involved_company_cache.extend(response.json())

    print("Saving involved companies id {} to {}...".format(start, end))
    with open("involved_companies.pkl", "wb") as f:
        pickle.dump(involved_company_cache, f)
        f.close()
    return 0

last_involved_company_id = max([involved_company["id"] for involved_company in involved_company_cache])
for i in range(last_involved_company_id, len(involved_company_ids), BATCH_SIZE):
    print("Getting involved companies from {} to {}...".format(i, i+BATCH_SIZE))
    get_involved_company(involved_company_ids[i], involved_company_ids[i+BATCH_SIZE])

# Export involved companies
with open("involved_companies.json", "w") as f:
    sorted_companies = sorted(involved_company_cache, key=lambda x: x["id"])
    json.dump(sorted_companies, f, sort_keys=True)
    f.close()
