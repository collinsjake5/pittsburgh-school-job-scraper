import { supabase, Job, ScrapeRun } from '@/lib/supabase'

export const revalidate = 60 // Revalidate every 60 seconds

async function getJobs(): Promise<Job[]> {
  const { data, error } = await supabase
    .from('jobs')
    .select('*')
    .eq('is_active', true)
    .order('first_seen_at', { ascending: false })

  if (error) {
    console.error('Error fetching jobs:', error)
    return []
  }

  return data || []
}

async function getRecentRuns(): Promise<ScrapeRun[]> {
  const { data, error } = await supabase
    .from('scrape_runs')
    .select('*')
    .order('started_at', { ascending: false })
    .limit(5)

  if (error) {
    console.error('Error fetching runs:', error)
    return []
  }

  return data || []
}

async function getStats() {
  const { count: totalJobs } = await supabase
    .from('jobs')
    .select('*', { count: 'exact', head: true })
    .eq('is_active', true)

  const { count: newThisWeek } = await supabase
    .from('jobs')
    .select('*', { count: 'exact', head: true })
    .eq('is_active', true)
    .gte('first_seen_at', new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString())

  const { data: districts } = await supabase
    .from('jobs')
    .select('district')
    .eq('is_active', true)

  const uniqueDistricts = new Set(districts?.map(d => d.district) || []).size

  return {
    totalJobs: totalJobs || 0,
    newThisWeek: newThisWeek || 0,
    uniqueDistricts,
  }
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function formatDateTime(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'success':
      return 'bg-green-100 text-green-800'
    case 'failed':
      return 'bg-red-100 text-red-800'
    case 'running':
      return 'bg-yellow-100 text-yellow-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

export default async function Home() {
  const [jobs, recentRuns, stats] = await Promise.all([
    getJobs(),
    getRecentRuns(),
    getStats(),
  ])

  return (
    <main className="max-w-6xl mx-auto px-4 py-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Pittsburgh School Jobs
        </h1>
        <p className="text-gray-600 mt-1">
          Social studies teaching positions in Pittsburgh area schools
        </p>
      </header>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-2xl font-bold text-blue-600">{stats.totalJobs}</div>
          <div className="text-gray-600">Active Positions</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-2xl font-bold text-green-600">{stats.newThisWeek}</div>
          <div className="text-gray-600">New This Week</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-2xl font-bold text-purple-600">{stats.uniqueDistricts}</div>
          <div className="text-gray-600">Districts with Openings</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Job Listings */}
        <div className="lg:col-span-2">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Current Openings
          </h2>
          {jobs.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
              No active positions found. Check back later!
            </div>
          ) : (
            <div className="space-y-4">
              {jobs.map((job) => (
                <div key={job.id} className="bg-white rounded-lg shadow p-4">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">{job.title}</h3>
                      <p className="text-sm text-gray-600">{job.district}</p>
                    </div>
                    <a
                      href={job.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="ml-4 px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                    >
                      Apply
                    </a>
                  </div>
                  <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                    <span>First seen: {formatDate(job.first_seen_at)}</span>
                    {job.portal_type && (
                      <span className="px-2 py-0.5 bg-gray-100 rounded">
                        {job.portal_type}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Scrape Runs */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Recent Scrapes
          </h2>
          {recentRuns.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
              No scrape runs yet
            </div>
          ) : (
            <div className="space-y-3">
              {recentRuns.map((run) => (
                <div key={run.id} className="bg-white rounded-lg shadow p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-gray-600">
                      {formatDateTime(run.started_at)}
                    </span>
                    <span className={`px-2 py-0.5 text-xs rounded ${getStatusColor(run.status)}`}>
                      {run.status}
                    </span>
                  </div>
                  {run.status === 'success' && (
                    <div className="text-sm">
                      <span className="text-gray-600">Found: </span>
                      <span className="font-medium">{run.total_jobs_found}</span>
                      {run.new_jobs_found > 0 && (
                        <span className="ml-2 text-green-600">
                          (+{run.new_jobs_found} new)
                        </span>
                      )}
                    </div>
                  )}
                  {run.status === 'failed' && run.error_message && (
                    <div className="text-sm text-red-600 truncate">
                      {run.error_message}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <footer className="mt-12 pt-8 border-t text-center text-gray-500 text-sm">
        Pittsburgh School Job Scraper | Automated daily at 9 AM ET
      </footer>
    </main>
  )
}
