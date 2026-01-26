import re
from urllib.parse import urljoin

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def scrape_schoolspring(url: str, district_name: str) -> list[dict]:
    """
    Scrape job listings from SchoolSpring career portals.
    SchoolSpring is a JavaScript-rendered SPA, requiring browser automation.
    """
    jobs = []

    if not PLAYWRIGHT_AVAILABLE:
        print(f"  Playwright not installed - skipping {district_name}")
        return jobs

    # Words that indicate non-job links
    exclude_patterns = [
        r'^open in',
        r'^report',
        r'^terms',
        r'^privacy',
        r'^help',
        r'^contact',
        r'^sign in',
        r'^sign up',
        r'^log in',
        r'^register',
        r'@.*\.(org|com|edu|net)',  # email addresses
        r'^google',
        r'^maps',
        r'^http',  # bare URLs
    ]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Navigate to the district's SchoolSpring page
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(4000)

            # Look for job listing elements - SchoolSpring uses specific patterns
            # Try to find job cards or listing containers
            job_containers = page.query_selector_all('[class*="job"], [class*="posting"], [class*="position"], [class*="vacancy"]')

            for container in job_containers:
                try:
                    title_elem = container.query_selector('h2, h3, h4, [class*="title"]')
                    if title_elem:
                        title = title_elem.inner_text().strip()
                        link = container.query_selector('a')
                        href = link.get_attribute('href') if link else ''

                        if title and len(title) > 3 and len(title) < 150:
                            # Check if this looks like a real job
                            if not any(re.search(p, title, re.I) for p in exclude_patterns):
                                job_url = urljoin(url, href) if href else url
                                jobs.append({
                                    'title': title,
                                    'district': district_name,
                                    'url': job_url,
                                    'source': 'SchoolSpring'
                                })
                except Exception:
                    continue

            # Alternative: look for links containing job-related keywords
            if not jobs:
                all_links = page.query_selector_all('a[href*="/job/"], a[href*="/posting/"], a[href*="jobID"]')
                for link in all_links:
                    try:
                        text = link.inner_text().strip()
                        href = link.get_attribute('href')

                        if text and len(text) > 3 and len(text) < 150:
                            if not any(re.search(p, text, re.I) for p in exclude_patterns):
                                job_url = urljoin(url, href)
                                jobs.append({
                                    'title': text,
                                    'district': district_name,
                                    'url': job_url,
                                    'source': 'SchoolSpring'
                                })
                    except Exception:
                        continue

            # If still no jobs, try to find any text that looks like a job posting
            if not jobs:
                # Look for common job title patterns in page text
                body = page.query_selector('body')
                if body:
                    text = body.inner_text()
                    job_patterns = [
                        r'(Teacher|Principal|Counselor|Secretary|Aide|Coach|Driver|Nurse|Custodian|Paraprofessional|Substitute|Assistant|Director|Coordinator|Specialist|Technician)[^,\n]{0,50}',
                    ]
                    for pattern in job_patterns:
                        matches = re.findall(pattern, text, re.I)
                        for match in matches[:10]:  # Limit to first 10
                            title = match.strip()
                            if len(title) > 5 and len(title) < 100:
                                if not any(re.search(p, title, re.I) for p in exclude_patterns):
                                    jobs.append({
                                        'title': title,
                                        'district': district_name,
                                        'url': url,
                                        'source': 'SchoolSpring'
                                    })

            browser.close()

    except Exception as e:
        print(f"  Error scraping {district_name}: {e}")

    # Deduplicate
    seen = set()
    unique_jobs = []
    for job in jobs:
        key = job['title'].lower()
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    return unique_jobs
