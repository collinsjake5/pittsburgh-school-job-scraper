#!/usr/bin/env python3
"""
Automated job scraper runner with notifications.
Run this script via cron to check for new jobs daily.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from scraper import load_config, scrape_all_districts, filter_jobs
from notify import send_notifications, send_test_notifications


def load_settings() -> dict:
    """Load notification settings."""
    settings_path = script_dir / 'settings.json'

    if not settings_path.exists():
        print("ERROR: settings.json not found!")
        print("Copy settings.example.json to settings.json and fill in your credentials.")
        sys.exit(1)

    with open(settings_path) as f:
        return json.load(f)


def load_previous_jobs() -> set:
    """Load job IDs from previous run."""
    cache_path = script_dir / '.job_cache.json'

    if not cache_path.exists():
        return set()

    try:
        with open(cache_path) as f:
            data = json.load(f)
            return set(data.get('job_ids', []))
    except:
        return set()


def save_current_jobs(jobs: list[dict]):
    """Save current job IDs for next run comparison."""
    cache_path = script_dir / '.job_cache.json'

    # Create unique ID for each job
    job_ids = []
    for job in jobs:
        job_id = f"{job['district']}|{job['title']}"
        job_ids.append(job_id)

    data = {
        'last_run': datetime.now().isoformat(),
        'job_count': len(jobs),
        'job_ids': job_ids
    }

    with open(cache_path, 'w') as f:
        json.dump(data, f, indent=2)


def get_new_jobs(current_jobs: list[dict], previous_ids: set) -> list[dict]:
    """Find jobs that weren't in the previous run."""
    new_jobs = []

    for job in current_jobs:
        job_id = f"{job['district']}|{job['title']}"
        if job_id not in previous_ids:
            new_jobs.append(job)

    return new_jobs


def run_scraper():
    """Main function to run automated scraper."""
    print(f"\n{'='*60}")
    print(f"Pittsburgh School Job Scraper - Automated Run")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # Load settings
    settings = load_settings()

    # Load district config
    config = load_config(script_dir / 'config.json')

    # Run scraper
    print("Scraping all districts for social studies positions...\n")
    all_jobs = scrape_all_districts(config, verbose=True)

    # Filter for social studies positions
    filtered_jobs = filter_jobs(all_jobs, social_studies_only=True)

    print(f"\nFound {len(filtered_jobs)} social studies position(s)")

    # Load previous jobs and find new ones
    previous_ids = load_previous_jobs()
    new_jobs = get_new_jobs(filtered_jobs, previous_ids)

    print(f"New since last run: {len(new_jobs)}")

    # Save current jobs for next run
    save_current_jobs(filtered_jobs)

    # Send notifications for new jobs
    if new_jobs:
        print(f"\n🎉 Found {len(new_jobs)} NEW position(s)!")
        for job in new_jobs:
            print(f"  • {job['title']} ({job['district']})")

        print("\nSending notifications...")
        results = send_notifications(new_jobs, settings)

        if results['email']:
            print("✓ Email sent")
        if results['push']:
            print("✓ Push notification sent")
    else:
        print("\nNo new positions since last run. No notifications sent.")

    # Save results to file
    output_path = script_dir / 'latest_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'scraped_at': datetime.now().isoformat(),
            'total_jobs': len(filtered_jobs),
            'new_jobs': len(new_jobs),
            'jobs': filtered_jobs
        }, f, indent=2)

    print(f"\nResults saved to: {output_path}")
    print(f"{'='*60}\n")

    return len(new_jobs)


def test_notifications():
    """Test notification configuration."""
    print("Testing notification configuration...")
    settings = load_settings()
    results = send_test_notifications(settings)

    print("\nResults:")
    print(f"  Email: {'✓ Success' if results['email'] else '✗ Failed'}")
    print(f"  Push:  {'✓ Success' if results['push'] else '✗ Failed'}")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        test_notifications()
    else:
        run_scraper()
