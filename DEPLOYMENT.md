# Deployment Guide

Deploy the Pittsburgh School Job Scraper to run automatically in the cloud.

## Architecture

```
GitHub Actions (9 AM daily)
        |
        v
   Python Scraper
        |
        v
    Supabase DB  <----  Vercel Dashboard
```

- **GitHub Actions**: Runs the scraper daily at 9 AM ET
- **Supabase**: Stores jobs and scrape history
- **Vercel**: Hosts the dashboard to view jobs

## Step 1: Set Up Supabase

1. Create a free account at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to **SQL Editor** and run the schema from `supabase/migrations/001_initial_schema.sql`
4. Go to **Settings > API** and note:
   - **Project URL** (e.g., `https://abcdef.supabase.co`)
   - **anon public** key (for the dashboard)
   - **service_role** key (for the scraper - keep this secret!)

## Step 2: Deploy Dashboard to Vercel

1. Push this repo to GitHub
2. Go to [vercel.com](https://vercel.com) and import the repo
3. Set the **Root Directory** to `web`
4. Add environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL` = your Supabase project URL
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` = your Supabase anon key
5. Deploy!

Your dashboard will be live at `your-project.vercel.app`

## Step 3: Configure GitHub Actions

1. Go to your GitHub repo > **Settings** > **Secrets and variables** > **Actions**
2. Add these **Repository secrets**:

| Secret Name | Value | Required |
|-------------|-------|----------|
| `SUPABASE_URL` | Your Supabase project URL | Yes |
| `SUPABASE_SERVICE_KEY` | Your Supabase service_role key | Yes |
| `EMAIL_FROM` | Gmail address to send from | Yes |
| `EMAIL_TO` | Email address to receive alerts | Yes |
| `EMAIL_PASSWORD` | Gmail app password (not your regular password) | Yes |
| `NTFY_TOPIC` | ntfy.sh topic for push notifications | No |

### Getting a Gmail App Password

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Enable 2-Factor Authentication if not already enabled
3. Go to **Security** > **App passwords**
4. Create a new app password for "Mail"
5. Use the 16-character password as `EMAIL_PASSWORD`

## Step 4: Test the Workflow

1. Go to your GitHub repo > **Actions**
2. Select "Daily Job Scraper"
3. Click **Run workflow** to test manually

You should see:
- Jobs appearing in your Supabase database
- Dashboard updating with new jobs
- Email notification if new jobs are found

## Scheduling

The scraper runs daily at 9:00 AM Eastern Time. To change this, edit `.github/workflows/scrape.yml`:

```yaml
schedule:
  - cron: '0 14 * * *'  # 14:00 UTC = 9:00 AM ET (winter)
```

Common cron examples:
- `'0 13 * * *'` - 9 AM ET (summer/EDT)
- `'0 14 * * *'` - 9 AM ET (winter/EST)
- `'0 14 * * 1-5'` - 9 AM ET, weekdays only
- `'0 14,18 * * *'` - 9 AM and 1 PM ET

## Local Development

### Dashboard (Next.js)

```bash
cd web
npm install
cp .env.example .env.local
# Edit .env.local with your Supabase credentials
npm run dev
```

Visit http://localhost:3001

### Scraper (Python)

The original `run_automated.py` still works for local testing with file-based caching.

To test the cloud version locally:

```bash
export SUPABASE_URL="your-url"
export SUPABASE_SERVICE_KEY="your-key"
export EMAIL_FROM="your-email"
export EMAIL_TO="your-email"
export EMAIL_PASSWORD="your-app-password"

python run_automated_cloud.py
```

## Troubleshooting

### GitHub Actions fails

1. Check the Actions logs for error messages
2. Verify all secrets are set correctly
3. Make sure Playwright can install (it needs ~100MB)

### No emails received

1. Verify `EMAIL_FROM`, `EMAIL_TO`, and `EMAIL_PASSWORD` secrets
2. Check Gmail for "blocked sign-in" security alerts
3. Make sure you're using an App Password, not your regular password

### Dashboard shows no data

1. Check Supabase dashboard to see if jobs table has data
2. Verify environment variables in Vercel
3. Check browser console for errors

### Scraper finds no jobs

1. Some districts may have changed their portal URLs
2. Check `config.json` for outdated URLs
3. Run locally with `--verbose` to see detailed output

## Costs

All services have generous free tiers:

- **Supabase**: 500MB database, 2GB bandwidth/month
- **Vercel**: 100GB bandwidth/month, unlimited deployments
- **GitHub Actions**: 2,000 minutes/month for private repos (unlimited for public)

For this scraper running once daily, you'll stay well within free limits.
