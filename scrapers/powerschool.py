import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re


def scrape_powerschool(url: str, district_name: str) -> list[dict]:
    """
    Scrape job listings from PowerSchool TalentEd (tedk12.com) career portals.
    These sites typically have an index.aspx with job categories and listings.
    """
    jobs = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

        # PowerSchool TalentEd typically uses divs with job listings
        # Look for job posting links
        job_links = soup.find_all('a', href=re.compile(r'(ViewJob|jobid|posting)', re.I))

        for link in job_links:
            title = link.get_text(strip=True)
            if title and len(title) > 2:
                job_url = urljoin(url, link.get('href', ''))
                jobs.append({
                    'title': title,
                    'district': district_name,
                    'url': job_url,
                    'source': 'PowerSchool'
                })

        # Alternative: look for elements with specific classes
        if not jobs:
            for elem in soup.find_all(['div', 'span', 'td'],
                                       class_=re.compile(r'(job|position|title)', re.I)):
                link = elem.find('a')
                if link:
                    title = link.get_text(strip=True)
                    if title and len(title) > 2:
                        job_url = urljoin(url, link.get('href', ''))
                        jobs.append({
                            'title': title,
                            'district': district_name,
                            'url': job_url,
                            'source': 'PowerSchool'
                        })

        # Look for list items with job postings
        if not jobs:
            for li in soup.find_all('li'):
                link = li.find('a')
                if link and link.get('href'):
                    href = link.get('href', '').lower()
                    if 'job' in href or 'posting' in href or 'position' in href:
                        title = link.get_text(strip=True)
                        if title and len(title) > 2:
                            job_url = urljoin(url, link.get('href', ''))
                            jobs.append({
                                'title': title,
                                'district': district_name,
                                'url': job_url,
                                'source': 'PowerSchool'
                            })

    except requests.RequestException as e:
        print(f"  Error fetching {district_name}: {e}")
    except Exception as e:
        print(f"  Error parsing {district_name}: {e}")

    # Deduplicate
    seen = set()
    unique_jobs = []
    for job in jobs:
        if job['url'] not in seen:
            seen.add(job['url'])
            unique_jobs.append(job)

    return unique_jobs
