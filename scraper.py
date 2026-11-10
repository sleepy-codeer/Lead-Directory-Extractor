
import requests
from bs4 import BeautifulSoup as bs
import argparse
from requests.exceptions import RequestException
import pandas as pd
from typing import TypedDict
import sys


class TeamRecord(TypedDict):
    name: str
    year: int
    win: int
    losses: int
    pct: float


parser = argparse.ArgumentParser(
    description="Scrape hockey team statistics from Scrape This Site.",
    epilog="Example: python scraper.py --search Boston Bruins"
)

parser.add_argument(
    '--search',
    nargs='*',
    default=None,
    help='Search for hockey teams by name. Leave empty to scrape all teams.'
)

args = parser.parse_args()

search_query = " ".join(args.search).strip().title() if args.search else ""

url = 'https://www.scrapethissite.com/pages/forms/'

records: list[TeamRecord] = []

params = {
    'q': search_query,
    'page_num': 1
}

session = requests.Session()

session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
})

while True:
    row_record = dict()

    try:
        response = session.get(url=url, timeout=8, params=params)
        response.raise_for_status()

    except RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        sys.exit(1)

    soup = bs(response.content, 'html.parser')

    table = soup.select_one('table.table')

    if not table:
        print("Table doesn't exist!")
        break

    if not table.find('td'):
        if params['page_num'] == 1:
            sys.exit("The team name you are searching doesn't exist")

        print("No more records found. Scraping completed!")
        break

    rows = table.select('tr.team')

    row_count = 0

    for row in rows:
        try:
            team_dict: TeamRecord = {
                cell.get('class')[0]: cell.get_text(strip=True)
                for cell in row.find_all('td')
                if cell.get('class')
            }

            row_count += 1

        except (TypeError, AttributeError):
            print('Skipping row: unexpected HTML formatting')
            continue

        team_dict.pop('ot-losses', None)
        team_dict.pop('gf', None)
        team_dict.pop('ga', None)
        team_dict.pop('diff', None)

        records.append(team_dict)

    print(f"Scraped page {params['page_num']} successfully. Scraped {row_count} records!")

    pages_ul = soup.select_one('ul.pagination')

    if not pages_ul:
        print('No pagination found. Scraping completed!')
        break

    pages = pages_ul.find_all('li')

    if not pages:
        print('Scraped all records successfully!')
        break

    page_number = [
        int(index.get_text(strip=True))
        for index in pages_ul.select('li a')
        if index.get_text(strip=True).isdigit()
    ]

    if not page_number:
        print('No numeric pagination links found.')
        break

    last_page = max(page_number)

    if params['page_num'] >= last_page:
        print('Scraped all records successfully!')
        break

    params['page_num'] += 1


if records:
    df = pd.DataFrame(records)
    df.to_csv(
        r"D:\Scraping\day8-hockey\output.csv",
        encoding="utf-8",
        index=False
    )

    print(f"\nTotal records scraped: {len(records)}")
    print("CSV exported successfully!")
