import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import axios from 'axios';  // Keep for backwards compatibility

interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  match_score: number;
  application_url: string;
  status: string;
}

interface HomePageProps {
  userId: number | null;
}

export default function HomePage({ userId }: HomePageProps) {
  const [topJobs, setTopJobs] = useState<Job[]>([]);
  const [resumeCount, setResumeCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!userId) { setLoading(false); return; }

    Promise.all([
      api.get(`/api/users/${userId}/jobs`).catch(() => ({ data: [] })),
      api.get(`/api/users/${userId}/resumes`).catch(() => ({ data: [] })),
    ]).then(([jobsRes, resumesRes]) => {
      const jobs = (jobsRes.data || []).sort((a: Job, b: Job) => (b.match_score || 0) - (a.match_score || 0)).slice(0, 5);
      setTopJobs(jobs);
      setResumeCount((resumesRes.data || []).length);
      setLoading(false);
    });
  }, [userId]);

  const avgMatch = topJobs.length > 0
    ? Math.round(topJobs.reduce((sum, j) => sum + (j.match_score || 0), 0) / topJobs.length)
    : 0;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-charcoal-50">Dashboard</h1>
        <p className="text-gray-600 dark:text-charcoal-400 mt-1">Your AI-powered job search overview</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        {[
          { label: 'Resumes', val: loading ? '—' : resumeCount, border: 'border-primary-500', text: 'text-primary-600 dark:text-primary-400' },
          { label: 'Jobs Found', val: loading ? '—' : topJobs.length, border: 'border-emerald-500', text: 'text-emerald-600 dark:text-emerald-400' },
          { label: 'Avg Match', val: loading ? '—' : `${avgMatch}%`, border: 'border-amber-500', text: 'text-amber-600 dark:text-amber-400' },
          { label: 'Saved/Applied', val: loading ? '—' : topJobs.filter(j => j.status === 'saved' || j.status === 'applied').length, border: 'border-violet-500', text: 'text-violet-600 dark:text-violet-400' },
        ].map((s, i) => (
          <div key={i} className={`bg-white dark:bg-charcoal-900 rounded-lg shadow dark:shadow-charcoal-950/50 p-6 border-l-4 ${s.border}`}>
            <div className="text-sm text-gray-500 dark:text-charcoal-400">{s.label}</div>
            <div className={`text-3xl font-bold mt-1 ${s.text}`}>{s.val}</div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        {[
          { to: '/resume', label: 'Upload Resume', desc: 'PDF analysis' },
          { to: '/jobs', label: 'Find Jobs', desc: 'AI web search' },
          { to: '/applications', label: 'Track Apps', desc: 'Manage pipeline' },
          { to: '/cover-letters', label: 'Cover Letters', desc: 'Auto-generate' },
        ].map((item, i) => {
          const colors = ['bg-primary-600 hover:bg-primary-700', 'bg-emerald-600 hover:bg-emerald-700', 'bg-violet-600 hover:bg-violet-700', 'bg-amber-600 hover:bg-amber-700'];
          return (
            <Link key={item.to} to={item.to} className={`${colors[i]} text-white rounded-lg p-5 transition-colors`}>
              <h3 className="font-semibold text-lg">{item.label}</h3>
              <p className="text-sm text-white/80 mt-1">{item.desc}</p>
            </Link>
          );
        })}
      </div>

      {/* Top Jobs */}
      <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow dark:shadow-charcoal-950/50">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-charcoal-700 flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-charcoal-50">Top Job Matches</h2>
          <Link to="/jobs" className="text-primary-600 dark:text-primary-400 hover:text-primary-800 dark:hover:text-primary-300 text-sm font-medium">View All →</Link>
        </div>

        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="text-gray-500 dark:text-charcoal-400 mt-3 text-sm">Loading jobs...</p>
          </div>
        ) : topJobs.length === 0 ? (
          <div className="p-12 text-center">
            <div className="text-5xl mb-4">🔍</div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-charcoal-50">No jobs found yet</h3>
            <p className="text-gray-500 dark:text-charcoal-400 mt-1">Upload your resume and search for matching positions</p>
            <Link to="/resume" className="inline-block mt-4 px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium">
              Upload Resume
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-charcoal-700">
            {topJobs.map(job => (
              <div key={job.id} className="p-6 hover:bg-gray-50 dark:hover:bg-charcoal-800 transition-colors">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-charcoal-50">{job.title}</h3>
                      <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        (job.match_score || 0) >= 80 ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300' :
                        (job.match_score || 0) >= 60 ? 'bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300' :
                        'bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-300'
                      }`}>
                        {job.match_score || 0}% Match
                      </span>
                    </div>
                    <p className="text-gray-600 dark:text-charcoal-300 mt-1">{job.company}</p>
                    <p className="text-sm text-gray-500 dark:text-charcoal-400 mt-1">📍 {job.location || 'Remote'}</p>
                  </div>
                  <a
                    href={job.application_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700"
                  >
                    Apply →
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
