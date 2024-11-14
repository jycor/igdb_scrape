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

# Get all company ids from involved_companies.json
print("Loading company ids from involved_companies.json...")
company_ids = set()
involved_companies = json.load(open("involved_companies.json", "r"))
for involved_company in involved_companies:
    if "company" not in involved_company:
        continue
    company_ids.add(involved_company["company"])

print("Total unique companies:", len(company_ids))
print("Estimated time {} seconds".format((len(company_ids) * DELAY) / BATCH_SIZE))

# Sort the ids
sorted_company_ids = sorted(list(company_ids))

COMPANY_URL = "https://api.igdb.com/v4/companies"
COMPANY_BATCH_QUERY = """
fields id, name;
where id >= {start} & id < {end};
limit 500;
"""
def load_company_cache():
    if not os.path.exists("companies.pkl"):
        return []
    with open("companies.pkl", "rb") as f:
        return pickle.load(f)

print("Loading company cache...")
company_cache = load_company_cache()
print("Loaded {} companies from cache...".format(len(company_cache)))

# It turns out it's possible that the API is missing results as we query
found_ids = set()
for company in company_cache:
    found_ids.add(company["id"])

def get_company_batch(start, end, batch_size=BATCH_SIZE):    
    query = COMPANY_BATCH_QUERY.format(start=start, end=end)
    # print("COMPANY QUERY:", query)

    time.sleep(DELAY)
    response = requests.post(COMPANY_URL, headers=HEADERS, data=query)
    if response.status_code != 200:
        print("COMPANY QUERY FAILED WITH:", response.status_code)
        print(response.json())
        return 1
    
    result = response.json()
    for company in result:
        found_ids.add(company["id"])
    
    company_cache.extend(result)
    # print("Saving companies id {} to {}...".format(start, end))
    with open("companies.pkl", "wb") as f:
        pickle.dump(company_cache, f)
    return 0

num_company_ids = len(sorted_company_ids)
for i in range(len(company_cache), num_company_ids, BATCH_SIZE):
    print("Getting batch {}/{}...".format(i/BATCH_SIZE, num_company_ids/BATCH_SIZE))
    get_company_batch(sorted_company_ids[i], sorted_company_ids[min(num_company_ids - 1, i+BATCH_SIZE)])

missing_ids = company_ids - found_ids
if len(missing_ids) > 0:
    print("Missing {} companies:".format(len(missing_ids)))
    print("Estimated time {} seconds".format(len(missing_ids) * DELAY))

COMPANY_QUERY = """
fields id, name;
where id = {id};
limit 1;
"""
def get_company(id):
    query = COMPANY_QUERY.format(id=id)
    # print("COMPANY QUERY:", query)

    time.sleep(DELAY)
    response = requests.post(COMPANY_URL, headers=HEADERS, data=query)
    if response.status_code != 200:
        print("COMPANY QUERY FAILED WITH:", response.status_code)
        print(response.json())
        return 1
    
    # must have exactly 1 result
    result = response.json()
    if len(result) == 0:
        print("ID {} NOT FOUND".format(id))
        return 1
    
    company_cache.extend(result)
    # print("Saving companies id {}...".format(id))
    with open("companies.pkl", "wb") as f:
        pickle.dump(company_cache, f)
    return 0

for missing_id in missing_ids:
    get_company(missing_id)

# Export companies
print("Exporting {} companies...".format(len(company_cache)))
with open("companies.json", "w") as f:
    sorted_companies = sorted(company_cache, key=lambda x: x["id"])
    json.dump(sorted_companies, f, sort_keys=True)
