import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Keywords to search for social studies positions
SOCIAL_STUDIES_SEARCH_TERMS = [
    'social studies',
    'history',
    'civics',
    'government',
    'economics',
    'geography',
    'humanities',
    'sociology',
    'psychology',
]


def scrape_applitrack(url: str, district_name: str, search_terms: list = None) -> list[dict]:
    """
    Scrape job listings from AppliTrack/Frontline career portals.
    Uses Playwright to search for specific terms and extract job listings.
    """
    jobs = []

    if not PLAYWRIGHT_AVAILABLE:
        return scrape_applitrack_basic(url, district_name)

    # Use social studies search terms by default
    if search_terms is None:
        search_terms = SOCIAL_STUDIES_SEARCH_TERMS

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Try searching for each term
            for term in search_terms:
                page.goto(url, wait_until='networkidle', timeout=30000)
                page.wait_for_timeout(2000)

                # Find and use the search box
                search_input = page.query_selector('#AppliTrackPostingSearch')
                if search_input:
                    search_input.fill(term)
                    page.click('#LnkBtnSearch')
                    page.wait_for_timeout(4000)

                    # Get page content after search
                    body_text = page.inner_text('body')

                    # Parse job listings - look for JobID patterns
                    # Job titles appear as standalone lines before "JobID:"
                    lines = body_text.split('\n')

                    for i, line in enumerate(lines):
                        line = line.strip()

                        # Look for job titles (line before JobID)
                        if i + 1 < len(lines) and 'JobID:' in lines[i + 1]:
                            title = line.strip()

                            if title and len(title) > 5 and len(title) < 200:
                                # Get position type from next few lines
                                position_type = ''
                                location = ''
                                for j in range(i + 1, min(i + 15, len(lines))):
                                    if 'Position Type:' in lines[j]:
                                        # Next non-empty line is the position type
                                        for k in range(j + 1, min(j + 3, len(lines))):
                                            if lines[k].strip():
                                                position_type = lines[k].strip()
                                                break
                                    if 'Location:' in lines[j]:
                                        for k in range(j + 1, min(j + 3, len(lines))):
                                            if lines[k].strip():
                                                location = lines[k].strip()
                                                break

                                jobs.append({
                                    'title': title,
                                    'position_type': position_type,
                                    'location': location,
                                    'district': district_name,
                                    'url': url,
                                    'search_term': term,
                                    'source': 'AppliTrack'
                                })

            browser.close()

    except Exception as e:
        print(f"  Error scraping {district_name}: {e}")
        return []

    # Deduplicate
    seen = set()
    unique_jobs = []
    for job in jobs:
        key = job['title'].lower()
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    return unique_jobs


def scrape_applitrack_basic(url: str, district_name: str) -> list[dict]:
    """Basic scraping without JavaScript rendering - returns categories."""
    jobs = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

        # Find category links
        category_links = soup.find_all('a', href=re.compile(r'Category='))

        for link in category_links:
            text = link.get_text(strip=True)
            match = re.match(r'(.+?)\s*\((\d+)\)$', text)
            if match:
                category = match.group(1)
                category_url = urljoin(url, link.get('href', ''))
                jobs.append({
                    'title': category,
                    'category': category,
                    'district': district_name,
                    'url': category_url,
                    'source': 'AppliTrack'
                })

    except Exception as e:
        print(f"  Error fetching {district_name}: {e}")

    return jobs
