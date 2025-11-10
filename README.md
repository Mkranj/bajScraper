# bajScrape

Scraping Bajs map data, to be used for visualizing usage and trends.

## Usage:

`python .\scraper.py -j "JSON" --max_jitter 1800`

Arguments:  
* --url: URL target to scrape.
* --json_folder: Folder in which to save received JSON files.
* --meta_file: JSON file to store metadata.
* --max_jitter: Maximum number of seconds to offset fetching.