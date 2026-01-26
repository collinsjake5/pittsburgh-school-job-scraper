import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re


def scrape_other(url: str, district_name: str) -> list[dict]:
    """
    Scrape job listings from custom/other district websites.
    Uses generic heuristics to find job postings.
    """
    jobs = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

        # Strategy 1: Look for links with job-related keywords in href or text
        job_keywords = ['job', 'position', 'opening', 'employment', 'career', 'vacancy',
                        'hiring', 'posting', 'opportunity', 'apply']

        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '').lower()
            text = link.get_text(strip=True).lower()

            # Skip navigation/menu links
            if len(text) < 3 or len(text) > 200:
                continue
            if text in ['home', 'about', 'contact', 'login', 'search']:
                continue

            # Check if this looks like a job posting link
            is_job_link = any(kw in href for kw in job_keywords)
            is_job_text = any(kw in text for kw in job_keywords)

            # Also look for common job title patterns
            job_title_patterns = [
                r'teacher', r'principal', r'secretary', r'aide', r'coach',
                r'custodian', r'driver', r'nurse', r'counselor', r'specialist',
                r'director', r'coordinator', r'assistant', r'paraprofessional',
                r'substitute', r'tutor', r'librarian', r'technician'
            ]
            is_job_title = any(re.search(p, text, re.I) for p in job_title_patterns)

            if is_job_link or is_job_title:
                title = link.get_text(strip=True)
                if title and len(title) > 2:
                    job_url = urljoin(url, link.get('href', ''))
                    jobs.append({
                        'title': title,
                        'district': district_name,
                        'url': job_url,
                        'source': 'District Website'
                    })

        # Strategy 2: Look for list items that might be job postings
        if not jobs:
            for li in soup.find_all('li'):
                text = li.get_text(strip=True)
                if any(re.search(p, text, re.I) for p in job_title_patterns):
                    link = li.find('a')
                    if link:
                        title = link.get_text(strip=True) or text[:100]
                        job_url = urljoin(url, link.get('href', ''))
                        jobs.append({
                            'title': title,
                            'district': district_name,
                            'url': job_url,
                            'source': 'District Website'
                        })
                    else:
                        # No link, just text
                        jobs.append({
                            'title': text[:100],
                            'district': district_name,
                            'url': url,
                            'source': 'District Website'
                        })

        # Strategy 3: Look for common page structures
        if not jobs:
            # Look for content divs
            content_divs = soup.find_all(['div', 'article', 'section'],
                                          class_=re.compile(r'(content|main|body)', re.I))
            for div in content_divs:
                paragraphs = div.find_all(['p', 'li', 'h2', 'h3', 'h4'])
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if any(re.search(pat, text, re.I) for pat in job_title_patterns):
                        link = p.find('a')
                        if link:
                            job_url = urljoin(url, link.get('href', ''))
                        else:
                            job_url = url
                        jobs.append({
                            'title': text[:100],
                            'district': district_name,
                            'url': job_url,
                            'source': 'District Website'
                        })

    except requests.RequestException as e:
        print(f"  Error fetching {district_name}: {e}")
    except Exception as e:
        print(f"  Error parsing {district_name}: {e}")

    # Deduplicate
    seen = set()
    unique_jobs = []
    for job in jobs:
        key = (job['title'], job['url'])
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    return unique_jobs
