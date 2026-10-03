import { useState, useEffect } from 'react';
import api from '../api';
import axios from 'axios';  // Keep for backwards compatibility

export default function Analytics({ userId }: { userId: number | null }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!userId) return;
    api.get(`/api/users/${userId}/analytics`).catch(() => ({ data: null }))
      .then(res => { setData(res.data); setLoading(false); });
  }, [userId]);

  if (loading) return <div className="p-8 text-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div></div>;
  if (!data) return <div className="p-8 text-center text-gray-500">No data available</div>;

  const statusColors: Record<string, string> = {
    new: 'bg-gray-200 text-gray-700', saved: 'bg-blue-200 text-blue-700',
    applied: 'bg-amber-200 text-amber-700', interviewing: 'bg-violet-200 text-violet-700',
    rejected: 'bg-red-200 text-red-700', offer: 'bg-emerald-200 text-emerald-700',
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-charcoal-50 mb-2">Application Analytics</h1>
      <p className="text-gray-600 dark:text-charcoal-400 mb-8">Insights into your job search</p>

      {/* Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow p-6">
          <div className="text-sm text-gray-500 dark:text-charcoal-400">Total Applications</div>
          <div className="text-3xl font-bold text-gray-900 dark:text-charcoal-50 mt-1">{data.total_applications}</div>
        </div>
        <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow p-6">
          <div className="text-sm text-gray-500 dark:text-charcoal-400">Avg Match Score</div>
          <div className="text-3xl font-bold text-primary-600 mt-1">{data.avg_match_score}%</div>
        </div>
        <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow p-6">
          <div className="text-sm text-gray-500 dark:text-charcoal-400">Avg Salary Min</div>
          <div className="text-3xl font-bold text-emerald-600 mt-1">{data.avg_salary_min ? `$${Math.round(data.avg_salary_min).toLocaleString()}` : 'N/A'}</div>
        </div>
        <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow p-6">
          <div className="text-sm text-gray-500 dark:text-charcoal-400">Avg Salary Max</div>
          <div className="text-3xl font-bold text-emerald-600 mt-1">{data.avg_salary_max ? `$${Math.round(data.avg_salary_max).toLocaleString()}` : 'N/A'}</div>
        </div>
      </div>

      {/* Status Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-charcoal-700"><h3 className="font-semibold text-gray-900 dark:text-charcoal-50">Status Breakdown</h3></div>
          <div className="p-6 space-y-3">
            {Object.entries(data.status_breakdown || {}).map(([status, count]) => (
              <div key={status} className="flex items-center justify-between">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold capitalize ${statusColors[status] || 'bg-gray-200 text-gray-700'}`}>{status}</span>
                <div className="flex items-center gap-3 flex-1 ml-4">
                  <div className="flex-1 bg-gray-200 dark:bg-charcoal-700 rounded-full h-2">
                    <div className="bg-primary-600 h-2 rounded-full" style={{ width: `${((count as number) / data.total_applications) * 100}%` }}></div>
                  </div>
                  <span className="text-sm font-medium text-gray-700 dark:text-charcoal-300 w-8 text-right">{count as number}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Companies */}
        <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-charcoal-700"><h3 className="font-semibold text-gray-900 dark:text-charcoal-50">Top Companies</h3></div>
          <div className="p-6 space-y-2">
            {(data.top_companies || []).slice(0, 8).map((c: any, i: number) => (
              <div key={i} className="flex justify-between text-sm">
                <span className="text-gray-700 dark:text-charcoal-300">{c.company}</span>
                <span className="text-gray-500 dark:text-charcoal-400 font-medium">{c.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Locations */}
      <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-charcoal-700"><h3 className="font-semibold text-gray-900 dark:text-charcoal-50">Top Locations</h3></div>
        <div className="p-6 flex flex-wrap gap-2">
          {(data.top_locations || []).slice(0, 15).map((l: any, i: number) => (
            <span key={i} className="px-3 py-1.5 bg-primary-100 dark:bg-primary-900/40 text-primary-800 dark:text-primary-300 rounded-full text-sm">{l.location} ({l.count})</span>
          ))}
        </div>
      </div>
    </div>
  );
}
