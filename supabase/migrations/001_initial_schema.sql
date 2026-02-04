-- Pittsburgh School Job Scraper - Supabase Schema
-- Run this in your Supabase SQL Editor to set up the database

-- Jobs table: stores all scraped job listings
CREATE TABLE IF NOT EXISTS jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    district TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    portal_type TEXT,
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    notified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint on district + title (our job ID logic)
    UNIQUE(district, title)
);

-- Scrape runs table: tracks each scraper execution
CREATE TABLE IF NOT EXISTS scrape_runs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT DEFAULT 'running', -- running, success, failed
    total_jobs_found INTEGER DEFAULT 0,
    new_jobs_found INTEGER DEFAULT 0,
    error_message TEXT,
    source TEXT DEFAULT 'github_actions' -- github_actions, manual, local
);

-- Notifications table: tracks sent notifications
CREATE TABLE IF NOT EXISTS notifications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    scrape_run_id UUID REFERENCES scrape_runs(id),
    notification_type TEXT NOT NULL, -- email, push
    jobs_count INTEGER NOT NULL,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);

-- Index for faster job lookups
CREATE INDEX IF NOT EXISTS idx_jobs_district_title ON jobs(district, title);
CREATE INDEX IF NOT EXISTS idx_jobs_active ON jobs(is_active);
CREATE INDEX IF NOT EXISTS idx_jobs_first_seen ON jobs(first_seen_at DESC);
CREATE INDEX IF NOT EXISTS idx_scrape_runs_started ON scrape_runs(started_at DESC);

-- Row Level Security (RLS) policies
-- Enable RLS on all tables
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- Policy: Allow read access for authenticated users and service role
CREATE POLICY "Allow read access" ON jobs FOR SELECT USING (true);
CREATE POLICY "Allow insert for service role" ON jobs FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow update for service role" ON jobs FOR UPDATE USING (true);

CREATE POLICY "Allow read access" ON scrape_runs FOR SELECT USING (true);
CREATE POLICY "Allow insert for service role" ON scrape_runs FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow update for service role" ON scrape_runs FOR UPDATE USING (true);

CREATE POLICY "Allow read access" ON notifications FOR SELECT USING (true);
CREATE POLICY "Allow insert for service role" ON notifications FOR INSERT WITH CHECK (true);

