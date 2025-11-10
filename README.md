# bajScrape

Scraping Bajs map data, to be used for visualizing usage and trends.

## Usage:

`python .\scraper.py -j "JSON" --max_jitter 1800`

Arguments:  
* --url: URL target to scrape.
* --json_folder: Folder in which to save received JSON files.
* --meta_file: JSON file to store metadata.
* --max_jitter: Maximum number of seconds to offset fetching.

## In Docker
Create an image using
`docker build --tag "mkranj/bajscrape" .`

Run this command to run the script inside a container, and retrieve the collected JSON to desired folder:  
`docker run --rm -v "$(pwd)/scraped_json:/JSON" mkranj/bajscrape`  

This will create a JSON file in the scraped_json folder each time the command is run.