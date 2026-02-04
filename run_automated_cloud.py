#!/usr/bin/env python3
"""
Cloud-based automated job scraper runner with Supabase integration.
Designed for GitHub Actions - stores results in Supabase instead of local files.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests

# Add parent directory to path for imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from scraper import load_config, scrape_all_districts, filter_jobs
from notify import send_status_email


def get_env_config() -> dict:
    """Load configuration from environment variables."""
    required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY']
    missing = [v for v in required_vars if not os.environ.get(v)]

    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

    return {
        'supabase_url': os.environ['SUPABASE_URL'],
        'supabase_key': os.environ['SUPABASE_SERVICE_KEY'],
        'email_from': os.environ.get('EMAIL_FROM'),
        'email_to': os.environ.get('EMAIL_TO'),
        'email_password': os.environ.get('EMAIL_PASSWORD'),
        'ntfy_topic': os.environ.get('NTFY_TOPIC'),
    }


class SupabaseClient:
    """Simple Supabase REST API client."""

    def __init__(self, url: str, key: str):
        self.url = url.rstrip('/')
        self.headers = {
            'apikey': key,
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }

    def _request(self, method: str, table: str, data: dict = None, params: dict = None):
        """Make a request to Supabase REST API."""
        url = f"{self.url}/rest/v1/{table}"
        response = requests.request(
            method,
            url,
            headers=self.headers,
            json=data,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        return response.json() if response.text else None

    def get_existing_job_ids(self) -> set:
        """Get all existing job IDs (district|title) from database."""
        params = {
            'select': 'district,title',
            'is_active': 'eq.true'
        }
        jobs = self._request('GET', 'jobs', params=params)
        return {f"{job['district']}|{job['title']}" for job in jobs}

    def create_scrape_run(self) -> str:
        """Create a new scrape run record and return its ID."""
        data = {'status': 'running', 'source': 'github_actions'}
        result = self._request('POST', 'scrape_runs', data=data)
        return result[0]['id']

    def update_scrape_run(self, run_id: str, status: str, total_jobs: int, new_jobs: int, error: str = None):
        """Update scrape run with results."""
        data = {
            'status': status,
            'completed_at': datetime.utcnow().isoformat(),
            'total_jobs_found': total_jobs,
            'new_jobs_found': new_jobs,
            'error_message': error
        }
        params = {'id': f'eq.{run_id}'}
        self._request('PATCH', 'scrape_runs', data=data, params=params)

    def upsert_jobs(self, jobs: list[dict]) -> list[dict]:
        """Insert or update jobs, return list of newly inserted jobs."""
        if not jobs:
            return []

        new_jobs = []
        for job in jobs:
            data = {
                'district': job['district'],
                'title': job['title'],
                'url': job['url'],
                'portal_type': job.get('portal_type'),
                'last_seen_at': datetime.utcnow().isoformat(),
                'is_active': True
            }

            # Try to insert, if conflict update last_seen_at
            headers = {**self.headers, 'Prefer': 'resolution=merge-duplicates,return=representation'}
            url = f"{self.url}/rest/v1/jobs"

            response = requests.post(
                url,
                headers=headers,
                json=data,
                params={'on_conflict': 'district,title'},
                timeout=30
            )

            if response.status_code == 201:
                # New job inserted
                result = response.json()
                if result and not result[0].get('notified'):
                    new_jobs.append({**job, 'id': result[0]['id']})
            elif response.status_code == 200:
                # Job updated (already existed)
                pass
            else:
                response.raise_for_status()

        return new_jobs

    def mark_jobs_notified(self, job_ids: list[str]):
        """Mark jobs as notified."""
        if not job_ids:
            return

        for job_id in job_ids:
            params = {'id': f'eq.{job_id}'}
            data = {'notified': True}
            self._request('PATCH', 'jobs', data=data, params=params)

    def mark_missing_jobs_inactive(self, current_job_keys: set):
        """Mark jobs not in current scrape as inactive."""
        # Get all active jobs
        params = {'select': 'id,district,title', 'is_active': 'eq.true'}
        active_jobs = self._request('GET', 'jobs', params=params)

        # Find jobs that weren't seen in this scrape
        for job in active_jobs:
            job_key = f"{job['district']}|{job['title']}"
            if job_key not in current_job_keys:
                params = {'id': f"eq.{job['id']}"}
                data = {'is_active': False}
                self._request('PATCH', 'jobs', data=data, params=params)

    def log_notification(self, run_id: str, notification_type: str, jobs_count: int, success: bool, error: str = None):
        """Log a notification attempt."""
        data = {
            'scrape_run_id': run_id,
            'notification_type': notification_type,
            'jobs_count': jobs_count,
            'success': success,
            'error_message': error
        }
        self._request('POST', 'notifications', data=data)


def run_scraper():
    """Main function to run cloud-based automated scraper."""
    print(f"\n{'='*60}")
    print(f"Pittsburgh School Job Scraper - Cloud Run")
    print(f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"{'='*60}\n")

    # Load configuration
    config = get_env_config()

    # Initialize Supabase client
    db = SupabaseClient(config['supabase_url'], config['supabase_key'])

    # Create scrape run record
    run_id = db.create_scrape_run()
    print(f"Started scrape run: {run_id}")

    try:
        # Load district config
        district_config = load_config(script_dir / 'config.json')

        # Run scraper
        print("\nScraping all districts for social studies positions...\n")
        all_jobs = scrape_all_districts(district_config, verbose=True)

        # Filter for social studies positions
        filtered_jobs = filter_jobs(all_jobs, social_studies_only=True)

        print(f"\nFound {len(filtered_jobs)} social studies position(s)")

        # Upsert jobs to database and get new ones
        new_jobs = db.upsert_jobs(filtered_jobs)

        print(f"New jobs: {len(new_jobs)}")

        # Mark jobs not in this scrape as inactive
        current_job_keys = {f"{job['district']}|{job['title']}" for job in filtered_jobs}
        db.mark_missing_jobs_inactive(current_job_keys)

        # Send status email (always, so user knows the scraper ran)
        if new_jobs:
            print(f"\nFound {len(new_jobs)} NEW position(s)!")
            for job in new_jobs:
                print(f"  - {job['title']} ({job['district']})")

        print("\nSending status email...")
        email_sent = send_status_email(len(filtered_jobs), len(new_jobs), new_jobs, config)

        if email_sent:
            print("Status email sent")
            db.log_notification(run_id, 'email', len(new_jobs), True)

            # Mark new jobs as notified
            if new_jobs:
                new_job_ids = [job['id'] for job in new_jobs if 'id' in job]
                db.mark_jobs_notified(new_job_ids)
        else:
            print("Failed to send status email")

        # Update scrape run as successful
        db.update_scrape_run(run_id, 'success', len(filtered_jobs), len(new_jobs))

        print(f"\n{'='*60}")
        print(f"Scrape completed successfully!")
        print(f"Total jobs: {len(filtered_jobs)}, New jobs: {len(new_jobs)}")
        print(f"{'='*60}\n")

        return len(new_jobs)

    except Exception as e:
        print(f"\nERROR: {e}")
        db.update_scrape_run(run_id, 'failed', 0, 0, str(e))
        raise


if __name__ == '__main__':
    run_scraper()
