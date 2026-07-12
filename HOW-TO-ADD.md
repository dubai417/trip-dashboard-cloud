# How to add a POI file to the Cloud — yourself

The "Cloud" is just this GitHub repo (`dubai417/trip-dashboard-cloud`). The app reads
`catalog.json` for the list of entries, and each entry points to a JSON file in `trips/`.
Adding a file = convert your CSV → JSON, add a catalog entry, push. The script
`add_to_cloud.py` does all three.

## The 3 steps (Terminal)

```bash
cd ~/Documents/claude/travel/TripDashboardApp/cloud

# 1. Convert + update the catalog + push, in one command:
python3 add_to_cloud.py "/path/to/My List.csv" --push
```

That's it. On the iPhone: **Cloud tab → Refresh** → the new entry appears → **Download**.

## Options

| What you want                        | Command                                                       |
| ------------------------------------ | ------------------------------------------------------------- |
| Custom display name                  | `python3 add_to_cloud.py "file.csv" --name "Tokyo Food" --push` |
| Skip a private list inside the file  | `python3 add_to_cloud.py "file.csv" --skip-list Family --push` |
| Convert only, push later             | omit `--push`, then `git add -A && git commit -m x && git push` |
| Update an existing entry             | just run it again with the same name — it replaces in place    |

## What the CSV needs

The enriched-list format (what all files in `Saved POI/updated POI/` already have):
`Title` is required; everything else is optional — `List, City/Country, Address, Cuisine,
Instagram, Famous For, What to Order, Getting There, Hotel/Floor, Good to Know, Note, URL,
Latitude, Longitude, Plus Code`. If there's a `List` column, each list becomes its own
**layer** in the app; otherwise the whole file is one layer.

## Remove an entry

Delete its file from `trips/`, delete its block from `catalog.json`, then
`git add -A && git commit -m "remove X" && git push`.

## ⚠️ Remember

This repo is **public** — anyone with the link can read every place, note, and coordinate.
Never add home locations, booking numbers, or personal notes (that's why the Family rows
were excluded from All POI).
