import { useState, useEffect } from 'react';
import axios from 'axios';

interface Job {
  id: number; title: string; company: string; location: string;
  job_type: string; match_score: number; match_reasons: string[];
  missing_skills: string[]; application_url: string; source: string; status: string;
  ease_of_apply: number; selected_for_bulk: boolean; description?: string;
  posted_date?: string;
}
interface Resume { id: number; filename: string; }

export default function JobDashboard({ userId }: { userId: number | null }) {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [selectedResume, setSelectedResume] = useState<number | null>(null);
  const [location, setLocation] = useState('Remote');
  const [locationType, setLocationType] = useState('any'); // remote, onsite, hybrid, any
  const [country, setCountry] = useState('');
  const [city, setCity] = useState('');
  const [worldwide, setWorldwide] = useState(false);
  const [hoursSincePosted, setHoursSincePosted] = useState(24); // Default: last 24 hours
  const [jobs, setJobs] = useState<Job[]>([]);
  const [scanning, setScanning] = useState(false);
  const [loading, setLoading] = useState(true);
  const [expandedJob, setExpandedJob] = useState<number | null>(null);
  const [viewingDescription, setViewingDescription] = useState<number | null>(null);
  const [minMatch, setMinMatch] = useState(0);
  const [jobType, setJobType] = useState('');
  const [companyFilter, setCompanyFilter] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [bulkStatus, setBulkStatus] = useState('');

  useEffect(() => {
    if (!userId) return;
    Promise.all([
      axios.get(`/api/users/${userId}/resumes`).catch(() => ({ data: [] })),
      axios.get(`/api/users/${userId}/jobs`).catch(() => ({ data: [] })),
    ]).then(([r, j]) => {
      setResumes(r.data || []);
      setJobs((j.data || []).sort((a: Job, b: Job) => (b.match_score || 0) - (a.match_score || 0)));
      if (r.data?.length > 0) setSelectedResume(r.data[0].id);
      setLoading(false);
    });
  }, [userId]);

  useEffect(() => {
    if (!userId || loading) return;
    const params: any = {};
    if (minMatch > 0) params.min_match = minMatch;
    if (jobType) params.job_type = jobType;
    if (companyFilter) params.company = companyFilter;
    axios.get(`/api/users/${userId}/jobs`, { params }).catch(() => ({ data: [] }))
      .then(res => setJobs((res.data || []).sort((a: Job, b: Job) => (b.match_score || 0) - (a.match_score || 0))));
  }, [minMatch, jobType, companyFilter, userId]);

  const handleScan = async () => {
    if (!selectedResume) return;
    setScanning(true);
    try {
      const { data } = await axios.post('/api/jobs/scan', {
        resume_id: selectedResume,
        location,
        location_type: locationType,
        country: country || undefined,
        city: city || undefined,
        worldwide,
        hours_since_posted: hoursSincePosted,
        max_results: 50
      });
      setJobs(data.sort((a: Job, b: Job) => (b.match_score || 0) - (a.match_score || 0)));
    } catch (err) { console.error(err); }
    finally { setScanning(false); }
  };

  const handleStatus = async (id: number, status: string) => {
    await axios.patch(`/api/jobs/${id}/status`, { status });
    setJobs(jobs.map(j => j.id === id ? { ...j, status } : j));
  };

  const handleBulk = async () => {
    if (!bulkStatus) return;
    const ids = jobs.filter(j => j.selected_for_bulk).map(j => j.id);
    if (ids.length === 0) return;
    await axios.post('/api/jobs/bulk-status', { status: bulkStatus, job_ids: ids });
    setJobs(jobs.map(j => j.selected_for_bulk ? { ...j, status: bulkStatus, selected_for_bulk: false } : j));
    setBulkStatus('');
  };

  const toggleBulk = async (id: number) => {
    await axios.post(`/api/jobs/${id}/select-bulk`);
    setJobs(jobs.map(j => j.id === id ? { ...j, selected_for_bulk: !j.selected_for_bulk } : j));
  };

  const shareJob = (job: Job) => {
    navigator.clipboard.writeText(`${job.title} at ${job.company}\n${job.location || 'Remote'} | ${job.job_type}\n${job.match_score}% match\n${job.application_url}`);
  };

  const formatPostedDate = (dateStr?: string) => {
    if (!dateStr) return 'Date unknown';
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffDays = Math.floor(diffHours / 24);
      
      if (diffHours < 1) return 'Posted just now';
      if (diffHours < 24) return `Posted ${diffHours}h ago`;
      if (diffDays === 1) return 'Posted 1 day ago';
      if (diffDays < 7) return `Posted ${diffDays} days ago`;
      return `Posted ${date.toLocaleDateString()}`;
    } catch {
      return 'Date unknown';
    }
  };

  const mc = (s: number) => s >= 80 ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300' : s >= 60 ? 'bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300' : 'bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-300';

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-charcoal-50 mb-2">Find Matching Jobs</h1>
      <p className="text-gray-600 dark:text-charcoal-400 mb-8">AI-powered job search based on your resume</p>

      <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow p-5 mb-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <select value={selectedResume || ''} onChange={e => { const v = parseInt(e.target.value, 10); setSelectedResume(isNaN(v) ? null : v); }} className="border border-gray-300 dark:border-charcoal-600 bg-white dark:bg-charcoal-800 text-gray-900 dark:text-charcoal-100 rounded-md px-3 py-2.5 text-sm">
            <option value="">Select resume...</option>
            {resumes.map(r => <option key={r.id} value={r.id}>{r.filename}</option>)}
          </select>
          <button onClick={handleScan} disabled={!selectedResume || scanning} className="bg-primary-600 text-white px-4 py-2.5 rounded-md hover:bg-primary-700 disabled:opacity-50 text-sm font-medium">{scanning ? '🔍 Searching...' : '🔍 Search Jobs'}</button>
        </div>

        {/* Location Type Selector */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-charcoal-300 mb-2">Job Type</label>
          <div className="flex flex-wrap gap-2">
            {[
              { value: 'any', label: 'Any', icon: '🌐' },
              { value: 'remote', label: 'Remote', icon: '🏠' },
              { value: 'onsite', label: 'On-site', icon: '🏢' },
              { value: 'hybrid', label: 'Hybrid', icon: '🔄' },
            ].map(type => (
              <button
                key={type.value}
                onClick={() => setLocationType(type.value)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  locationType === type.value
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 dark:bg-charcoal-800 text-gray-700 dark:text-charcoal-300 hover:bg-gray-200 dark:hover:bg-charcoal-700'
                }`}
              >
                {type.icon} {type.label}
              </button>
            ))}
          </div>
        </div>

        {/* Location Inputs */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-charcoal-400 mb-1">Country (Optional)</label>
            <input
              type="text"
              value={country}
              onChange={e => setCountry(e.target.value)}
              className="w-full border border-gray-300 dark:border-charcoal-600 bg-white dark:bg-charcoal-800 text-gray-900 dark:text-charcoal-100 rounded-md px-3 py-2 text-sm"
              placeholder="e.g. USA, UAE, Germany"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-charcoal-400 mb-1">City (Optional)</label>
            <input
              type="text"
              value={city}
              onChange={e => setCity(e.target.value)}
              className="w-full border border-gray-300 dark:border-charcoal-600 bg-white dark:bg-charcoal-800 text-gray-900 dark:text-charcoal-100 rounded-md px-3 py-2 text-sm"
              placeholder="e.g. Dubai, New York"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-charcoal-400 mb-1">Worldwide Search</label>
            <div className="flex items-center h-9">
              <input
                type="checkbox"
                checked={worldwide}
                onChange={e => setWorldwide(e.target.checked)}
                className="w-4 h-4 text-primary-600 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm text-gray-700 dark:text-charcoal-300">Search globally</span>
            </div>
          </div>
        </div>

        {/* Time Filter */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-charcoal-300 mb-2">Job Posting Date</label>
          <div className="flex flex-wrap gap-2">
            {[
              { value: 24, label: 'Last 24 Hours' },
              { value: 72, label: 'Last 3 Days' },
              { value: 168, label: 'Last 7 Days' },
            ].map(time => (
              <button
                key={time.value}
                onClick={() => setHoursSincePosted(time.value)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  hoursSincePosted === time.value
                    ? 'bg-emerald-600 text-white'
                    : 'bg-gray-100 dark:bg-charcoal-800 text-gray-700 dark:text-charcoal-300 hover:bg-gray-200 dark:hover:bg-charcoal-700'
                }`}
              >
                {time.label}
              </button>
            ))}
          </div>
        </div>

        <button onClick={() => setShowFilters(!showFilters)} className="w-full px-3 py-2 border border-gray-300 dark:border-charcoal-600 text-gray-700 dark:text-charcoal-300 rounded-md text-sm hover:bg-gray-50 dark:hover:bg-charcoal-800">
          {showFilters ? 'Hide' : 'Show'} Additional Filters
        </button>
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-charcoal-700 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 dark:text-charcoal-400 mb-1">Min Match %</label>
              <input type="range" min="0" max="100" value={minMatch} onChange={e => setMinMatch(parseInt(e.target.value))} className="w-full" />
              <span className="text-sm text-gray-700 dark:text-charcoal-300">{minMatch}%+</span>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 dark:text-charcoal-400 mb-1">Job Type</label>
              <select value={jobType} onChange={e => setJobType(e.target.value)} className="w-full border border-gray-300 dark:border-charcoal-600 bg-white dark:bg-charcoal-800 text-gray-900 dark:text-charcoal-100 rounded-md px-3 py-2 text-sm">
                <option value="">All</option><option value="Remote">Remote</option><option value="Hybrid">Hybrid</option><option value="On-site">On-site</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 dark:text-charcoal-400 mb-1">Company</label>
              <input type="text" value={companyFilter} onChange={e => setCompanyFilter(e.target.value)} className="w-full border border-gray-300 dark:border-charcoal-600 bg-white dark:bg-charcoal-800 text-gray-900 dark:text-charcoal-100 rounded-md px-3 py-2 text-sm" placeholder="Filter by company..." />
            </div>
          </div>
        )}
      </div>

      {jobs.length > 0 && (
        <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow p-4 mb-4 flex items-center gap-3">
          <span className="text-sm text-gray-700 dark:text-charcoal-300 font-medium">Bulk:</span>
          <span className="text-xs text-gray-500 dark:text-charcoal-400">{jobs.filter(j => j.selected_for_bulk).length} selected</span>
          <select value={bulkStatus} onChange={e => setBulkStatus(e.target.value)} className="border border-gray-300 dark:border-charcoal-600 bg-white dark:bg-charcoal-800 text-gray-900 dark:text-charcoal-100 rounded px-2 py-1 text-sm">
            <option value="">Set status...</option><option value="saved">Saved</option><option value="applied">Applied</option>
            <option value="interviewing">Interviewing</option><option value="rejected">Rejected</option>
          </select>
          <button onClick={handleBulk} disabled={!bulkStatus} className="px-3 py-1 bg-primary-600 text-white rounded text-sm hover:bg-primary-700 disabled:opacity-50">Apply</button>
        </div>
      )}

      {scanning && (
        <div className="bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
            <div><p className="text-primary-700 dark:text-primary-300 font-medium">Searching for jobs...</p><p className="text-sm text-primary-600 dark:text-primary-400">Analyzing job boards with AI</p></div>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {loading ? (
          <div className="p-8 text-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div><p className="mt-3 text-gray-500 dark:text-charcoal-400 text-sm">Loading...</p></div>
        ) : jobs.length === 0 ? (
          <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow p-12 text-center">
            <div className="text-5xl mb-4">🔍</div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-charcoal-50">No jobs found yet</h3>
            <p className="text-gray-500 dark:text-charcoal-400 mt-1">Select a resume and search for matching positions</p>
          </div>
        ) : jobs.map(job => (
          <div key={job.id} className="bg-white dark:bg-charcoal-900 rounded-lg shadow hover:shadow-md transition-shadow">
            <div className="p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <input type="checkbox" checked={job.selected_for_bulk || false} onChange={() => toggleBulk(job.id)} className="mt-1.5 w-4 h-4 text-primary-600 border-gray-300 rounded" />
                  <div>
                    <div className="flex items-center gap-3">
                      <h3 className="text-base font-semibold text-gray-900 dark:text-charcoal-50">{job.title}</h3>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${mc(job.match_score || 0)}`}>{job.match_score || 0}%</span>
                      {job.ease_of_apply >= 70 && <span className="px-2 py-0.5 bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300 rounded text-xs font-medium">Easy Apply</span>}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-charcoal-300 mt-0.5">{job.company}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-gray-500 dark:text-charcoal-400">
                      <span>📍 {job.location || 'Remote'}</span>
                      {job.job_type && <span>💼 {job.job_type}</span>}
                      <span>🕒 {formatPostedDate(job.posted_date)}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <button onClick={() => shareJob(job)} className="px-2.5 py-1.5 text-xs border border-gray-300 dark:border-charcoal-600 text-gray-600 dark:text-charcoal-300 rounded hover:bg-gray-50 dark:hover:bg-charcoal-800" title="Copy">📋</button>
                  <button onClick={() => setExpandedJob(expandedJob === job.id ? null : job.id)} className="px-2.5 py-1.5 text-xs border border-gray-300 dark:border-charcoal-600 text-gray-600 dark:text-charcoal-300 rounded hover:bg-gray-50 dark:hover:bg-charcoal-800">{expandedJob === job.id ? 'Hide' : 'Details'}</button>
                  <a href={job.application_url} target="_blank" rel="noopener noreferrer" className="px-3 py-1.5 text-xs bg-primary-600 text-white rounded hover:bg-primary-700 font-medium">Apply →</a>
                </div>
              </div>
              {expandedJob === job.id && (
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-charcoal-700 space-y-4">
                  {job.match_reasons?.length > 0 && (
                    <div><h4 className="text-sm font-medium text-gray-700 dark:text-charcoal-300 mb-2">✅ Why this matches</h4>
                      <ul className="space-y-1">{job.match_reasons.map((r, idx) => <li key={idx} className="text-sm text-gray-600 dark:text-charcoal-400">• {r}</li>)}</ul>
                    </div>
                  )}
                  {job.missing_skills?.length > 0 && (
                    <div><h4 className="text-sm font-medium text-gray-700 dark:text-charcoal-300 mb-2">⚠️ Missing Skills</h4>
                      <div className="flex flex-wrap gap-2">{job.missing_skills.map((s, idx) => <span key={idx} className="px-2 py-1 bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300 rounded text-xs font-medium">{s}</span>)}</div>
                    </div>
                  )}
                  {job.description && (
                    <div>
                      <button
                        onClick={() => setViewingDescription(viewingDescription === job.id ? null : job.id)}
                        className="text-sm text-primary-600 dark:text-primary-400 hover:underline font-medium mb-2"
                      >
                        {viewingDescription === job.id ? 'Hide Full Description' : 'View Full Description'}
                      </button>
                      {viewingDescription === job.id && (
                        <div className="mt-2 p-4 bg-gray-50 dark:bg-charcoal-800 rounded-md max-h-96 overflow-y-auto">
                          <pre className="whitespace-pre-wrap text-sm text-gray-700 dark:text-charcoal-300 font-sans">
                            {job.description}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                  <div className="flex gap-2">
                    <span className="text-sm text-gray-700 dark:text-charcoal-300">Status:</span>
                    <select value={job.status || 'new'} onChange={e => handleStatus(job.id, e.target.value)} className="border border-gray-300 dark:border-charcoal-600 bg-white dark:bg-charcoal-800 text-gray-900 dark:text-charcoal-100 rounded px-2 py-1 text-sm">
                      {['new', 'saved', 'applied', 'interviewing', 'rejected', 'offer'].map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                    <a href="/interview" className="ml-auto text-sm text-primary-600 dark:text-primary-400 hover:underline">🎯 Interview Prep →</a>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
