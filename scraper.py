# polite_scraper.py
import requests
import time
import json
import random
import os
from datetime import datetime, timezone
import argparse

# Default values if no arguments provided:
URL = "https://maps.nextbike.net/maps/nextbike-live.json?city=1172&domains=hd&list_cities=0&bikes=0"
FOLDER_TO_SAVE = "json"
META_FILE = "data_meta.json"

USER_AGENT = "BajScraper/1.0"
JSON_FILENAME_START = "bajs"


# Maximum seconds to offset hourly retrieval
MAX_JITTER = 1800

# Backoff parameters
MAX_RETRIES = 5
BASE_BACKOFF = 2.0  # seconds
MAX_BACKOFF = 300.0  # max backoff

def load_meta(metadata_file):
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, "r") as f:
                return json.load(f)
        except BaseException:
            return {}
    return {}

def save_meta(meta, metadata_file):
    with open(metadata_file, "w") as f:
        json.dump(meta, f)

def save_data_json(data, json_file_start, target_folder = ""):
    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")

    filename = json_file_start + "_" + str(timestamp) + ".json"

    if (target_folder != ""):
        filename = os.path.join(target_folder, filename)

        if not os.path.isdir(target_folder):
            os.mkdir(target_folder)

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[{datetime.now().isoformat()}] saved data to {filename}")

def fetch_data(url, useragent, metadata_file, json_file_start, target_folder):
    meta = load_meta(metadata_file)
    headers = {
        "User-Agent": useragent,
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
        # conditional headers if previously saved
    }
    if "etag" in meta:
        headers["If-None-Match"] = meta["etag"]
    if "last_modified" in meta:
        headers["If-Modified-Since"] = meta["last_modified"]

    session = requests.Session()
    session.headers.update(headers)

    attempt = 0
    while attempt <= MAX_RETRIES:
        try:
            resp = session.get(url, timeout=30)
        except requests.RequestException as e:
            # network error -> backoff and retry
            attempt += 1
            backoff = min(MAX_BACKOFF, BASE_BACKOFF * (2 ** (attempt - 1)))
            backoff *= random.uniform(0.8, 1.2)  # jitter
            print(f"Network error: {e}. retry {attempt}/{MAX_RETRIES} after {backoff:.1f}s")
            time.sleep(backoff)
            continue

        # Handle 200 OK, 304 Not Modified, 429, 5xx, etc.
        if resp.status_code == 200:
            # parse and save JSON
            try:
                data = resp.json()
            except ValueError:
                print("Received non-JSON response")
                return False
            save_data_json(data, json_file_start, target_folder)

            # save ETag / Last-Modified if present
            meta = {}
            if resp.headers.get("ETag"):
                meta["etag"] = resp.headers["ETag"]
            if resp.headers.get("Last-Modified"):
                meta["last_modified"] = resp.headers["Last-Modified"]
            # also store timestamp
            meta["fetched_at"] = datetime.now(timezone.utc).isoformat()
            save_meta(meta, metadata_file)
            return True

        elif resp.status_code == 304:
            # Not modified — nothing to do
            print(f"[{datetime.now().isoformat()}] 304 Not Modified; no update")
            # update fetched_at timestamp
            meta["fetched_at"] = datetime.now(timezone.utc).isoformat()
            save_meta(meta, metadata_file)
            return True

        elif resp.status_code == 429:
            # Too Many Requests -> use Retry-After if present
            retry_after = resp.headers.get("Retry-After")
            if retry_after:
                try:
                    wait = int(retry_after)
                except ValueError:
                    # sometimes Retry-After can be a http-date; fallback
                    wait = BASE_BACKOFF * (2 ** attempt)
            else:
                wait = min(MAX_BACKOFF, BASE_BACKOFF * (2 ** attempt))
            wait *= random.uniform(0.8, 1.2)
            print(f"429 received. Waiting {wait:.1f}s before retry.")
            time.sleep(wait)
            attempt += 1
            continue

        elif 500 <= resp.status_code < 600:
            # Server error -> exponential backoff
            attempt += 1
            backoff = min(MAX_BACKOFF, BASE_BACKOFF * (2 ** (attempt - 1)))
            backoff *= random.uniform(0.8, 1.2)
            print(f"Server error {resp.status_code}. retry {attempt}/{MAX_RETRIES} after {backoff:.1f}s")
            time.sleep(backoff)
            continue

        else:
            print(f"Unexpected status {resp.status_code}. Response body: {resp.text[:200]}")
            return False

    print("Max retries reached, giving up for now.")
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser("bajScrape")

    parser.add_argument("-u", "--url", help = "URL target to scrape.")
    parser.add_argument("-j", "--json_folder", help = "Folder in which to save recieved JSON files.")
    parser.add_argument("-m", "--meta_file", help = "JSON file to store metadata.")
    parser.add_argument("--max_jitter", help = "Maximum number of seconds to offset fetching.")
    
    args = parser.parse_args()

    if args.url is not None:
        target_url = args.url
    else:
        target_url = URL

    if args.meta_file is not None:
        meta = args.meta_file
    else:
        meta = META_FILE

    if args.json_folder is not None:
        json_folder = args.json_folder
    else:
        json_folder = FOLDER_TO_SAVE
        
    if args.max_jitter is not None:
        jitter_m = int(args.max_jitter)
    else:
        jitter_m = MAX_JITTER

    # Add a small startup jitter if you run this hourly across many machines
    STARTUP_JITTER = random.uniform(0, jitter_m)
    print(f"Startup jitter {STARTUP_JITTER:.1f}s")
    time.sleep(STARTUP_JITTER)

    success = fetch_data(target_url, USER_AGENT, meta, JSON_FILENAME_START, json_folder)
    if success:
        print("Fetch finished successfully")
    else:
        print("Fetch failed")