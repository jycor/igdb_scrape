import json

games = json.load(open("games.json", "r"))
companies = json.load(open("companies.json", "r"))
involved_companies = json.load(open("involved_companies.json", "r"))
covers = json.load(open("covers.json", "r"))

expected = set()
for game in games:
    if "involved_companies" not in game:
        continue
    for involved_company in game["involved_companies"]:
        expected.add(involved_company)
    
for involved_company in involved_companies:
    expected.discard(involved_company["id"])

if len(expected) > 0:
    diff = sorted(list(expected))
    print("Missing {} involved companies:\n{}".format(len(diff), diff))
else:
    print("All involved companies are present in involved_companies.json")

expected = set()
for involved_company in involved_companies:
    if "company" not in involved_company:
        continue
    expected.add(involved_company["company"])

for company in companies:
    expected.discard(company["id"])

if len(expected) > 0:
    diff = sorted(list(expected))
    print("Missing {} companies:\n{}".format(len(diff), diff))
else:
    print("All companies are present in companies.json")

expected = set()
for game in games:
    if "cover" not in game:
        continue
    expected.add(game["cover"])

for cover in covers:
    expected.discard(cover["id"])

if len(expected) > 0:
    diff = sorted(list(expected))
    print("Missing {} covers:\n{}".format(len(diff), diff))
else:
    print("All covers are present in covers.json")