import re
from urllib.parse import urljoin

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def scrape_paeducator(url: str, district_name: str, district_filter: str = None) -> list[dict]:
    """
    Scrape job listings from PAEducator.net.
    PAEducator is a JavaScript-rendered SPA for Pennsylvania educator jobs.
    """
    jobs = []
    search_term = district_filter or district_name

    if not PLAYWRIGHT_AVAILABLE:
        print(f"  Playwright not installed - skipping {district_name}")
        return jobs

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Navigate to PAEducator search page
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(3000)

            # Find the keyword search input and search for the district
            search_input = page.query_selector('input')
            if search_input:
                search_input.fill(search_term)
                search_input.press('Enter')
                page.wait_for_timeout(4000)

            # Get the page text to parse job listings
            body = page.query_selector('body')
            if body:
                page_text = body.inner_text()

                # Parse job listings - they appear as text blocks
                # Pattern: County, Job Title, Contract Type, Date Posted, Deadline
                lines = page_text.split('\n')

                current_job = {}
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line:
                        continue

                    # Check if this line mentions our district
                    if search_term.lower() in line.lower():
                        # This line contains our district, it's likely a job title
                        # Look backwards for context
                        title = line
                        # Try to extract just the job title (remove district suffix if present)
                        if ' - ' in title and search_term.lower() in title.lower():
                            parts = title.rsplit(' - ', 1)
                            if search_term.lower() in parts[-1].lower():
                                title = parts[0].strip()

                        jobs.append({
                            'title': title[:150],
                            'district': district_name,
                            'url': url,
                            'source': 'PAEducator'
                        })

            # Alternative: try to find links with job details
            job_links = page.query_selector_all('a[href*="/job/"], a[href*="/posting/"]')
            for link in job_links:
                try:
                    text = link.inner_text().strip()
                    href = link.get_attribute('href')

                    # Check if related to our district
                    parent_text = link.evaluate('el => el.closest("div")?.innerText || ""')
                    if search_term.lower() in text.lower() or search_term.lower() in parent_text.lower():
                        if text and len(text) > 2 and len(text) < 200:
                            job_url = urljoin(url, href) if href else url
                            jobs.append({
                                'title': text,
                                'district': district_name,
                                'url': job_url,
                                'source': 'PAEducator'
                            })
                except Exception:
                    continue

            browser.close()

    except Exception as e:
        print(f"  Error scraping {district_name} from PAEducator: {e}")

    # Deduplicate
    seen = set()
    unique_jobs = []
    for job in jobs:
        key = job['title'].lower()
        if key not in seen and len(job['title']) > 3:
            seen.add(key)
            unique_jobs.append(job)

    return unique_jobs
