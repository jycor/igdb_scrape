This is a python script that scrapes the IGDB for every game they have.
Follow instructions from [here](https://api-docs.igdb.com/#getting-started) to get your `CLIENT_ID` and `SECRET`.

Then, add them to `.env` file in the format:
```
CLIENT_ID="your_client_id"
SECRET="your_secret"
```

Run `python get_auth.py` to get the access token (it will be saved in `.env`).

Run with `python3 scrape.py`.

1. Run `python games_genres_platforms.pt` to get games, genres, and platforms.
2. Run `python involved_companies.py` to get involved companies.
3. Run `python companies.py` to get actual company names.
4. Run `python covers.py` to get actual covers.
5. Run `python upload.py` to upload to the database.

`validate.py` will show all missing ids from involved_companies, companies, and covers.

If you ever need to reset something, just delete any generated `.pkl` files.
Delete the `.json` files too for a hard reset.