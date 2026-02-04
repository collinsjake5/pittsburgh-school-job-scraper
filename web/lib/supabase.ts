import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export type Job = {
  id: string
  district: string
  title: string
  url: string
  portal_type: string | null
  first_seen_at: string
  last_seen_at: string
  is_active: boolean
  notified: boolean
  created_at: string
}

export type ScrapeRun = {
  id: string
  started_at: string
  completed_at: string | null
  status: 'running' | 'success' | 'failed'
  total_jobs_found: number
  new_jobs_found: number
  error_message: string | null
  source: string
}
