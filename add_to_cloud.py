#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add a POI CSV to the Trip Dashboard Cloud (kind:"places" catalog entry).

Usage:
    python3 add_to_cloud.py "path/to/list.csv"                       # convert + update catalog
    python3 add_to_cloud.py "path/to/list.csv" --name "My List"      # custom display name
    python3 add_to_cloud.py "path/to/list.csv" --push                # also git commit + push
    python3 add_to_cloud.py "list.csv" --skip-list Family            # drop rows of one List

CSV columns understood (the enriched-list schema; extra columns are ignored):
    Title (required) · List · City/Country · Address · Cuisine · Instagram · Famous For
    What to Order · Getting There · Hotel/Floor · Good to Know · Note · URL
    Latitude · Longitude · Plus Code

The app groups places into layers by `category` = the List column (falls back to the
file's display name), so a combined file with a List column imports with one layer
per original list.

Run it from anywhere; it always writes into this repo (the folder containing this script).
"""
import argparse, csv, json, os, re, subprocess, sys
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.abspath(__file__))

def slug(s):
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE).strip().lower()
    s = re.sub(r"[\s_]+", "-", s)
    return s or "list"

def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("--name", help="display name (default: CSV filename)")
    ap.add_argument("--id", help="catalog id (default: slug of the name)")
    ap.add_argument("--skip-list", action="append", default=[],
                    help="drop rows whose List column equals this (repeatable)")
    ap.add_argument("--push", action="store_true", help="git add+commit+push when done")
    a = ap.parse_args()

    name = a.name or os.path.splitext(os.path.basename(a.csv_path))[0]
    cid = a.id or slug(name)
    skip = {s.strip().lower() for s in a.skip_list}

    places, lists_seen, skipped = [], [], 0
    with open(a.csv_path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            title = (r.get("Title") or "").strip()
            if not title:
                continue
            lst = (r.get("List") or "").strip()
            if lst.lower() in skip:
                skipped += 1
                continue
            if lst and lst not in lists_seen:
                lists_seen.append(lst)
            g = lambda c: (r.get(c) or "").strip()
            p = {
                # the 14 required string fields — always present, even when empty
                "name": title,
                "area": g("City/Country"),
                "category": lst or name,
                "cuisine": g("Cuisine"),
                "near": g("Getting There"),
                "map": g("URL"),
                "order": g("What to Order"),
                "why": "",
                "price": "",
                "booking": "",
                "social": g("Instagram"),
                "socialURL": "",
                "notes": g("Note"),
                "source": lst,
            }
            # optional fields — only when non-empty
            for key, col in [("city", "City/Country"), ("famousFor", "Famous For"),
                             ("setting", "Hotel/Floor"), ("goodToKnow", "Good to Know"),
                             ("address", "Address"), ("plusCode", "Plus Code")]:
                if g(col):
                    p[key] = g(col)
            lat, lon = fnum(r.get("Latitude")), fnum(r.get("Longitude"))
            if lat is not None and lon is not None:
                p["lat"], p["lon"] = lat, lon
            places.append(p)

    if not places:
        sys.exit("No places found — is this the right CSV?")

    trip = {"plans": [{"id": cid, "cloudID": cid, "name": name, "currency": "AED", "places": places}]}
    data_path = f"trips/{cid}.json"
    with open(os.path.join(REPO, data_path), "w", encoding="utf-8") as f:
        json.dump(trip, f, ensure_ascii=False, indent=1)

    desc = f"{len(places)} places"
    if lists_seen:
        desc += " · " + " · ".join(lists_seen[:6]) + (" · …" if len(lists_seen) > 6 else "")
    entry = {
        "id": cid, "name": name, "dateRange": desc, "days": 1, "places": len(places),
        "kind": "places",
        "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dataPath": data_path,
    }
    cat_path = os.path.join(REPO, "catalog.json")
    with open(cat_path, encoding="utf-8") as f:
        catalog = json.load(f)
    catalog["trips"] = [t for t in catalog["trips"] if t.get("id") != cid]
    catalog["trips"].insert(0, entry)
    with open(cat_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    kb = os.path.getsize(os.path.join(REPO, data_path)) // 1024
    print(f"✓ {name}: {len(places)} places ({len(lists_seen) or 1} layers, {kb} KB)"
          + (f" — skipped {skipped} rows of {sorted(skip)}" if skipped else ""))
    print(f"  wrote {data_path} + catalog entry '{cid}'")

    if a.push:
        subprocess.run(["git", "-C", REPO, "add", "-A"], check=True)
        subprocess.run(["git", "-C", REPO, "commit", "-m", f"cloud: add/update {name} ({len(places)} places)"], check=True)
        subprocess.run(["git", "-C", REPO, "push"], check=True)
        print("✓ pushed — the app's Cloud tab will show it after Refresh")
    else:
        print("Not pushed. To publish:  git -C", REPO, "add -A && git commit -m 'update' && git push")

if __name__ == "__main__":
    main()
