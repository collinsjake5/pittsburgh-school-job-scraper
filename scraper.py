#!/usr/bin/env python3
"""
Pittsburgh Area School District Job Scraper

Scrapes job listings from 20 school districts in the Pittsburgh area.
Supports AppliTrack, PowerSchool, PAEducator, and custom district websites.
"""

import json
import argparse
import re
from datetime import datetime
from pathlib import Path

from scrapers import scrape_applitrack, scrape_powerschool, scrape_paeducator, scrape_schoolspring, scrape_other


# Keywords for social studies positions
SOCIAL_STUDIES_KEYWORDS = [
    'social studies',
    'history',
    'civics',
    'government',
    'economics',
    'geography',
    'political science',
    'world cultures',
    'american studies',
    'global studies',
    'us history',
    'world history',
    'american history',
    'ap history',
    'ap government',
    'ap economics',
    # Additional terms
    'humanities',
    'sociology',
    'psychology',
    'current events',
]

# Keywords for middle/high school (grades 6-12)
SECONDARY_KEYWORDS = [
    'middle school',
    'high school',
    'secondary',
    'junior high',
    '6th grade', '7th grade', '8th grade',
    '9th grade', '10th grade', '11th grade', '12th grade',
    'grade 6', 'grade 7', 'grade 8',
    'grade 9', 'grade 10', 'grade 11', 'grade 12',
    '6-12', '7-12', '6-8', '9-12',
]

# Keywords to exclude (elementary only)
EXCLUDE_KEYWORDS = [
    'elementary school',
    'primary school',
    'kindergarten',
    'pre-k',
    'prek',
    'preschool',
    '1st grade', '2nd grade', '3rd grade', '4th grade', '5th grade',
    'grade 1', 'grade 2', 'grade 3', 'grade 4', 'grade 5',
    'k-5', 'k-6', 'k-4', 'k-3',
]


def is_social_studies_job(job: dict) -> bool:
    """Check if a job is related to social studies.

    Checks title, position_type, location, category, and search_term fields.
    """
    # Combine all available text fields for matching
    title = job.get('title', '').lower()
    position_type = job.get('position_type', '').lower()
    location = job.get('location', '').lower()
    category = job.get('category', '').lower()
    search_term = job.get('search_term', '').lower()

    combined_text = f"{title} {position_type} {location} {category}"

    # Check if any social studies keyword appears in combined text
    if any(kw in combined_text for kw in SOCIAL_STUDIES_KEYWORDS):
        return True

    # Also include if it was found via a social studies search term
    if search_term and any(kw in search_term for kw in SOCIAL_STUDIES_KEYWORDS):
        return True

    return False


def is_teaching_position(job: dict) -> bool:
    """Check if a job is a teaching position (not aide/support staff)."""
    title = job.get('title', '').lower()
    position_type = job.get('position_type', '').lower()

    # Exclude non-teaching positions
    exclude_types = [
        'aide', 'paraprofessional', 'assistant', 'pca',
        'custodian', 'maintenance', 'cafeteria', 'food service',
        'secretary', 'clerical', 'bus driver', 'transportation',
        'nurse', 'support staff'
    ]

    combined = title + ' ' + position_type
    if any(ex in combined for ex in exclude_types):
        # But include if it's explicitly a teaching position
        if 'teacher' in combined or 'instructor' in combined:
            return True
        return False

    return True


def is_secondary_level(job: dict) -> bool:
    """Check if a job is for middle/high school (not elementary)."""
    title = job.get('title', '').lower()
    location = job.get('location', '').lower()
    combined = title + ' ' + location

    # If explicitly elementary, exclude
    if any(kw in combined for kw in EXCLUDE_KEYWORDS):
        return False

    # If explicitly secondary, include
    if any(kw in combined for kw in SECONDARY_KEYWORDS):
        return True

    # If no grade level specified, include it (could be any level)
    # This catches generic "Social Studies Teacher" postings
    return True


def filter_jobs(jobs: list[dict], social_studies_only: bool = False) -> list[dict]:
    """Filter jobs based on criteria."""
    if not social_studies_only:
        return jobs

    filtered = []
    for job in jobs:
        # Must be social studies related
        if not is_social_studies_job(job):
            continue

        # Must be a teaching position
        if not is_teaching_position(job):
            continue

        # Must be secondary level (or unspecified)
        if not is_secondary_level(job):
            continue

        filtered.append(job)

    return filtered


def load_config(config_path: str = 'config.json') -> dict:
    """Load the configuration file with school district information."""
    with open(config_path, 'r') as f:
        return json.load(f)


def scrape_district(school: dict) -> list[dict]:
    """Scrape jobs from a single school district based on its type."""
    name = school['name']
    site_type = school['type']
    jobs = []

    if site_type == 'AppliTrack':
        jobs = scrape_applitrack(school['url'], name)

    elif site_type == 'PowerSchool':
        jobs = scrape_powerschool(school['url'], name)

    elif site_type == 'PAEducator':
        district_filter = school.get('paeducator_filter', name)
        jobs = scrape_paeducator(school['url'], name, district_filter)

    elif site_type == 'SchoolSpring':
        jobs = scrape_schoolspring(school['url'], name)

    elif site_type == 'Other':
        jobs = scrape_other(school['url'], name)

    elif site_type == 'Multiple':
        # Handle districts with multiple career portals
        for portal in school.get('urls', []):
            portal_type = portal['type']
            portal_url = portal['url']

            if portal_type == 'AppliTrack':
                jobs.extend(scrape_applitrack(portal_url, name))
            elif portal_type == 'PowerSchool':
                jobs.extend(scrape_powerschool(portal_url, name))

    return jobs


def scrape_all_districts(config: dict, verbose: bool = True) -> list[dict]:
    """Scrape jobs from all configured school districts."""
    all_jobs = []

    for school in config['schools']:
        name = school['name']
        if verbose:
            print(f"Scraping {name}...")

        jobs = scrape_district(school)
        all_jobs.extend(jobs)

        if verbose:
            print(f"  Found {len(jobs)} job(s)")

    return all_jobs


def save_results(jobs: list[dict], output_path: str = None) -> str:
    """Save results to a JSON file."""
    if output_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f'jobs_{timestamp}.json'

    output = {
        'scraped_at': datetime.now().isoformat(),
        'total_jobs': len(jobs),
        'jobs': jobs
    }

    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    return output_path


def print_summary(jobs: list[dict]):
    """Print a summary of scraped jobs."""
    print("\n" + "=" * 60)
    print("SCRAPING COMPLETE")
    print("=" * 60)

    # Count by district
    by_district = {}
    for job in jobs:
        district = job['district']
        by_district[district] = by_district.get(district, 0) + 1

    print(f"\nTotal jobs found: {len(jobs)}")
    print("\nJobs by district:")
    for district, count in sorted(by_district.items()):
        print(f"  {district}: {count}")

    # Count by source
    by_source = {}
    for job in jobs:
        source = job['source']
        by_source[source] = by_source.get(source, 0) + 1

    print("\nJobs by source type:")
    for source, count in sorted(by_source.items()):
        print(f"  {source}: {count}")


def print_jobs(jobs: list[dict]):
    """Print all job listings."""
    print("\n" + "=" * 60)
    print("JOB LISTINGS")
    print("=" * 60)

    current_district = None
    for job in sorted(jobs, key=lambda x: x['district']):
        if job['district'] != current_district:
            current_district = job['district']
            print(f"\n--- {current_district} ---")

        print(f"  * {job['title']}")
        print(f"    {job['url']}")


def main():
    parser = argparse.ArgumentParser(
        description='Scrape job listings from Pittsburgh area school districts'
    )
    parser.add_argument(
        '-c', '--config',
        default='config.json',
        help='Path to config file (default: config.json)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output JSON file path (default: jobs_TIMESTAMP.json)'
    )
    parser.add_argument(
        '-d', '--district',
        help='Scrape only a specific district by name'
    )
    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='List all job titles in output'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress progress output'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save results to file'
    )
    parser.add_argument(
        '--social-studies',
        action='store_true',
        help='Only show middle/high school social studies positions'
    )

    args = parser.parse_args()

    # Load configuration
    script_dir = Path(__file__).parent
    config_path = script_dir / args.config
    config = load_config(config_path)

    # Filter to specific district if requested
    if args.district:
        matching = [s for s in config['schools']
                   if args.district.lower() in s['name'].lower()]
        if not matching:
            print(f"No district found matching '{args.district}'")
            print("Available districts:")
            for school in config['schools']:
                print(f"  - {school['name']}")
            return 1
        config['schools'] = matching

    # Run scraper
    verbose = not args.quiet
    jobs = scrape_all_districts(config, verbose=verbose)

    # Apply filters
    if args.social_studies:
        jobs = filter_jobs(jobs, social_studies_only=True)
        if verbose:
            print(f"\nFiltered to middle/high school social studies positions")

    # Print summary
    print_summary(jobs)

    # List all jobs if requested
    if args.list:
        print_jobs(jobs)

    # Save results
    if not args.no_save:
        output_path = save_results(jobs, args.output)
        print(f"\nResults saved to: {output_path}")

    return 0


if __name__ == '__main__':
    exit(main())
