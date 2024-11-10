This is a python script that scrapes the IGDB for every game they have.
Follow instructions from [here](https://api-docs.igdb.com/#getting-started) to get your `CLIENT_ID` and `SECRET`.

Then, add them to `.env` file in the format:
```
CLIENT_ID=your_client_id
SECRET=your_secret
```

Run `python get_auth.py` to get the access token (it will be saved in `.env`).

Run with `python3 scrape.py`.

If you ever need to reset something, just delete any generated `.pkl` files.
Delete the `.json` files too for a hard reset.