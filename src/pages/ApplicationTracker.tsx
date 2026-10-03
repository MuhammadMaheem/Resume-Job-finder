import { useState, useEffect } from 'react';
import api from '../api';
import axios from 'axios';  // Keep for backwards compatibility

interface Job { id: number; title: string; company: string; location: string; match_score: number; application_url: string; status: string; created_at: string; }

export default function ApplicationTracker({ userId }: { userId: number | null }) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    if (!userId) return;
    api.get(`/api/users/${userId}/jobs`).catch(() => ({ data: [] }))
      .then(res => { setJobs(res.data || []); setLoading(false); });
  }, [userId]);

  const handleStatus = async (jobId: number, status: string) => {
    await api.patch(`/api/jobs/${jobId}/status`, { status });
    setJobs(jobs.map(j => j.id === jobId ? { ...j, status } : j));
  };

  const exportToCSV = () => {
    const headers = ['Title', 'Company', 'Location', 'Match Score', 'Status', 'Applied Date', 'Application URL'];
    const rows = jobs.map(job => [
      job.title,
      job.company,
      job.location,
      job.match_score,
      job.status,
      job.created_at ? new Date(job.created_at).toLocaleDateString() : 'N/A',
      job.application_url
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `job_applications_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const filtered = filter === 'all' ? jobs : jobs.filter(j => j.status === filter);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-charcoal-50">Application Tracker</h1>
          <p className="text-gray-600 dark:text-charcoal-400">Track your job applications</p>
        </div>
        <button
          onClick={exportToCSV}
          className="bg-emerald-600 text-white px-4 py-2 rounded-md hover:bg-emerald-700 text-sm font-medium transition-colors"
        >
          📊 Export to CSV
        </button>
      </div>
      <div className="mb-8"></div>

      <div className="grid grid-cols-5 gap-4 mb-6">
        {[
          { label: 'Total', val: jobs.length, c: 'text-gray-900 dark:text-charcoal-50' },
          { label: 'Saved', val: jobs.filter(j => j.status === 'saved').length, c: 'text-blue-600 dark:text-blue-400' },
          { label: 'Applied', val: jobs.filter(j => j.status === 'applied').length, c: 'text-amber-600 dark:text-amber-400' },
          { label: 'Interviewing', val: jobs.filter(j => j.status === 'interviewing').length, c: 'text-violet-600 dark:text-violet-400' },
          { label: 'Offers', val: jobs.filter(j => j.status === 'offer').length, c: 'text-emerald-600 dark:text-emerald-400' },
        ].map(s => (
          <button key={s.label} onClick={() => setFilter(s.label.toLowerCase() === 'total' ? 'all' : s.label.toLowerCase())}
            className={`bg-white dark:bg-charcoal-900 rounded-lg shadow p-4 text-center border-2 transition-colors ${filter === (s.label.toLowerCase() === 'total' ? 'all' : s.label.toLowerCase()) ? 'border-primary-500' : 'border-transparent dark:border-charcoal-700'}`}>
            <div className={`text-2xl font-bold ${s.c}`}>{s.val}</div>
            <div className="text-sm text-gray-500 dark:text-charcoal-400">{s.label}</div>
          </button>
        ))}
      </div>

      <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-8 text-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div></div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center text-gray-500 dark:text-charcoal-400">No applications found</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200 dark:divide-charcoal-700">
            <thead className="bg-gray-50 dark:bg-charcoal-800">
              <tr>
                {['Job', 'Location', 'Match', 'Status', 'Actions'].map(h => (
                  <th key={h} className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-charcoal-400 uppercase">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-charcoal-900 divide-y divide-gray-200 dark:divide-charcoal-700">
              {filtered.map(job => (
                <tr key={job.id} className="hover:bg-gray-50 dark:hover:bg-charcoal-800">
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900 dark:text-charcoal-50">{job.title}</div>
                    <div className="text-sm text-gray-500 dark:text-charcoal-400">{job.company}</div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500 dark:text-charcoal-400">{job.location || 'Remote'}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-block px-2 py-1 rounded-full text-xs font-semibold ${(job.match_score || 0) >= 80 ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300' : (job.match_score || 0) >= 60 ? 'bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300' : 'bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-300'}`}>{job.match_score || 0}%</span>
                  </td>
                  <td className="px-6 py-4">
                    <select value={job.status || 'new'} onChange={e => handleStatus(job.id, e.target.value)} className="border border-gray-300 dark:border-charcoal-600 bg-white dark:bg-charcoal-800 text-gray-900 dark:text-charcoal-100 rounded px-2 py-1 text-sm">
                      {['new', 'saved', 'applied', 'interviewing', 'rejected', 'offer'].map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </td>
                  <td className="px-6 py-4"><a href={job.application_url} target="_blank" rel="noopener noreferrer" className="text-primary-600 dark:text-primary-400 hover:text-primary-800 dark:hover:text-primary-300 text-sm font-medium">View →</a></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
