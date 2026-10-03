import { useState, useEffect } from 'react';
import api from '../api';
import axios from 'axios';  // Keep for backwards compatibility

interface Resume { id: number; filename: string; analysis: any; }

export default function ResumeCompare({ userId }: { userId: number | null }) {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [comparison, setComparison] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!userId) return;
    api.get(`/api/users/${userId}/resumes/compare`).catch(() => ({ data: { resumes: [], comparison: null } }))
      .then(res => { setResumes(res.data.resumes || []); setComparison(res.data.comparison); setLoading(false); });
  }, [userId]);

  if (loading) return <div className="p-8 text-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div></div>;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-charcoal-50 mb-2">Resume Comparison</h1>
      <p className="text-gray-600 dark:text-charcoal-400 mb-8">Compare your resumes side by side</p>

      {resumes.length < 2 ? (
        <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow p-12 text-center">
          <div className="text-5xl mb-4">📄</div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-charcoal-50">Need at least 2 resumes</h3>
          <p className="text-gray-500 dark:text-charcoal-400 mt-1">Upload more resumes to compare them</p>
        </div>
      ) : (
        <>
          {/* Side by side */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {resumes.map(r => (
              <div key={r.id} className="bg-white dark:bg-charcoal-900 rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-charcoal-700">
                  <h3 className="font-semibold text-gray-900 dark:text-charcoal-50">{r.filename}</h3>
                </div>
                <div className="p-5 space-y-3 text-sm">
                  <div><span className="text-gray-500 dark:text-charcoal-400">Skills:</span> <span className="text-gray-900 dark:text-charcoal-300">{r.analysis?.skills?.length || 0}</span></div>
                  <div><span className="text-gray-500 dark:text-charcoal-400">Seniority:</span> <span className="text-gray-900 dark:text-charcoal-300 capitalize">{r.analysis?.seniority_level || '—'}</span></div>
                  <div><span className="text-gray-500 dark:text-charcoal-400">Experience:</span> <span className="text-gray-900 dark:text-charcoal-300">{r.analysis?.years_of_experience || '—'} yrs</span></div>
                  <div>
                    <span className="text-gray-500 dark:text-charcoal-400">Top Skills:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {(r.analysis?.skills || []).slice(0, 8).map((s: string, i: number) => (
                        <span key={i} className="px-2 py-0.5 bg-primary-100 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300 rounded text-xs">{s}</span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Common & Unique Skills */}
          {comparison && (
            <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-charcoal-700"><h3 className="font-semibold text-gray-900 dark:text-charcoal-50">Skill Analysis</h3></div>
              <div className="p-6">
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-emerald-700 dark:text-emerald-400 mb-2">Common Skills ({comparison.common_skills?.length || 0})</h4>
                  <div className="flex flex-wrap gap-2">
                    {(comparison.common_skills || []).map((s: string, i: number) => (
                      <span key={i} className="px-3 py-1 bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300 rounded-full text-sm">{s}</span>
                    ))}
                  </div>
                </div>
                {(comparison.unique_skills_per_resume || []).map((u: any, i: number) => (
                  <div key={i} className="mb-4">
                    <h4 className="text-sm font-medium text-amber-700 dark:text-amber-400 mb-2">Unique to {u.filename}</h4>
                    <div className="flex flex-wrap gap-2">
                      {(u.unique_skills || []).map((s: string, j: number) => (
                        <span key={j} className="px-3 py-1 bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300 rounded-full text-sm">{s}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
