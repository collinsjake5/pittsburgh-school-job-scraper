# Pittsburgh Area School District Job Scraper

Automated job scraper that monitors 20 Pittsburgh area school districts for teaching positions. Built specifically to find **middle/high school social studies** positions and send email notifications when new jobs are posted.

## Features

- Scrapes 20 school districts across 4 different job portal types
- Filters for secondary-level (grades 6+) social studies teaching positions
- Detects new job postings and avoids duplicate notifications
- Email notifications via Gmail
- Automated daily scheduling via cron
- Handles JavaScript-rendered sites using Playwright

## Supported Districts

| District | Portal Type |
|----------|-------------|
| Mt. Lebanon | AppliTrack |
| Bethel Park | AppliTrack |
| Moon Area | AppliTrack |
| Canon-McMillan | AppliTrack |
| Brentwood | AppliTrack |
| North Allegheny | AppliTrack |
| North Hills | AppliTrack |
| Upper St. Clair | SchoolSpring |
| South Park | SchoolSpring |
| South Fayette | SchoolSpring |
| Peters Township | PAEducator |
| Chartiers Valley | PAEducator |
| West Allegheny | PAEducator |
| Keystone Oaks | PAEducator |
| Baldwin-Whitehall | PAEducator |
| Carlynton | PAEducator |
| Montour | District Website |
| Fort Cherry | District Website |
| Chartiers-Houston | District Website |
| Trinity Area | District Website |

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/collinsjake5/pittsburgh-school-job-scraper.git
cd pittsburgh-school-job-scraper
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Playwright browser

```bash
python -m playwright install chromium
```

## Quick Start

### Run the scraper manually

```bash
# Scrape all districts and filter for social studies positions
python scraper.py --social-studies

# Scrape all districts (all jobs, no filter)
python scraper.py

# Scrape a specific district
python scraper.py --district "Mt. Lebanon"

# List all job titles found
python scraper.py -l

# Save to a specific output file
python scraper.py -o my_jobs.json

# Run quietly (no progress output)
python scraper.py -q
```

## Setting Up Automated Notifications

### Option 1: Interactive Setup (Recommended)

```bash
python setup_automation.py
```

This wizard will guide you through:
- Email notification setup (Gmail)
- Optional phone push notifications (ntfy.sh)
- Automatic daily scheduling (cron)

### Option 2: Manual Setup

#### Step 1: Create settings file

```bash
cp settings.example.json settings.json
```

#### Step 2: Configure Gmail

Edit `settings.json`:

```json
{
  "email_from": "your.email@gmail.com",
  "email_to": "your.email@gmail.com",
  "email_password": "your-gmail-app-password"
}
```

**To get a Gmail App Password:**
1. Enable 2-Factor Authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Create a new app password for "Mail"
4. Copy the 16-character password (spaces are fine)

#### Step 3: Test notifications

```bash
python run_automated.py --test
```

#### Step 4: Set up daily automation

Add to crontab for daily 7 AM checks:

```bash
crontab -e
```

Add this line:
```
0 7 * * * /usr/bin/python3 /path/to/pittsburgh-school-job-scraper/run_automated.py >> /path/to/pittsburgh-school-job-scraper/cron.log 2>&1
```

## How It Works

### Job Filtering

The `--social-studies` flag filters for positions matching these criteria:

**Included keywords:**
- social studies, history, civics, government, economics, geography
- world history, american history, us history, political science

**Excluded keywords:**
- elementary, primary, k-5, k-4, k-3
- aide, paraprofessional, assistant, substitute

**Grade level detection:**
- Includes: middle school, high school, secondary, grades 6-12, junior high
- Excludes: elementary, primary school

### Job Caching

The automated runner (`run_automated.py`) maintains a cache of previously seen jobs in `.job_cache.json`. This ensures:
- You only get notified about NEW positions
- No duplicate emails for the same job posting
- Efficient tracking across multiple runs

### Portal Types

| Type | Technology | Notes |
|------|------------|-------|
| **AppliTrack** | Playwright + BeautifulSoup | Uses search functionality to find relevant positions |
| **SchoolSpring** | Playwright | JavaScript SPA, requires browser automation |
| **PAEducator** | Playwright | Statewide PA job board, filters by district |
| **District Website** | BeautifulSoup | Generic scraper for custom district sites |

## File Structure

```
pittsburgh-school-job-scraper/
├── scraper.py              # Main scraper with CLI
├── config.json             # District URLs and portal types
├── notify.py               # Email/push notification functions
├── run_automated.py        # Automated runner with caching
├── setup_automation.py     # Interactive setup wizard
├── settings.json           # Your notification credentials (git-ignored)
├── settings.example.json   # Template for settings
├── requirements.txt        # Python dependencies
├── .gitignore              # Git ignore rules
├── scrapers/
│   ├── __init__.py
│   ├── applitrack.py       # AppliTrack portal scraper
│   ├── schoolspring.py     # SchoolSpring portal scraper
│   ├── paeducator.py       # PAEducator portal scraper
│   ├── powerschool.py      # PowerSchool portal scraper
│   └── other.py            # Generic district website scraper
└── .job_cache.json         # Cache of seen jobs (git-ignored)
```

## Output Format

Results are saved as JSON:

```json
{
  "scraped_at": "2024-01-25T10:30:00",
  "total_jobs": 3,
  "jobs": [
    {
      "title": "Social Studies Teacher - High School",
      "district": "Mt. Lebanon",
      "url": "https://...",
      "source": "AppliTrack"
    }
  ]
}
```

## Useful Commands

```bash
# Run scraper with social studies filter
python scraper.py --social-studies

# Run automated check (sends email if new jobs found)
python run_automated.py

# Send a test email
python run_automated.py --test

# View automation log
tail -f cron.log

# Check cron jobs
crontab -l

# Edit cron jobs
crontab -e
```

## Troubleshooting

### "Playwright not installed"
```bash
pip install playwright
python -m playwright install chromium
```

### "Email failed to send"
- Verify your Gmail App Password is correct
- Make sure 2FA is enabled on your Google account
- Check that `settings.json` has the correct email addresses

### "No jobs found"
- This is normal if there are no current social studies openings
- Try running without `--social-studies` to see all jobs
- Check individual district websites to verify the scraper is working

### Cron job not running
- Check the cron log: `tail -f cron.log`
- Verify python path: `which python3`
- Make sure the script has execute permissions: `chmod +x run_automated.py`

## Requirements

- Python 3.9+
- Playwright (for JavaScript-rendered sites)
- BeautifulSoup4 (for HTML parsing)
- Requests (for HTTP requests)

## Privacy & Security

- `settings.json` contains your email credentials and is git-ignored
- Never commit your `settings.json` file
- Use Gmail App Passwords, not your main password
- The settings file is automatically set to owner-only permissions (600)

## License

MIT License - feel free to use and modify for your own job search needs.
