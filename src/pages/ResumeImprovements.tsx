import { useState, useEffect } from 'react';
import api from '../api';
import axios from 'axios';  // Keep for backwards compatibility

interface Resume { id: number; filename: string; }
interface Imp { missing_keywords: string[]; skill_gaps: string[]; suggestions: string[]; recommended_certifications: string[]; trending_skills: string[]; }

export default function ResumeImprovements({ userId }: { userId: number | null }) {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [imp, setImp] = useState<Imp | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!userId) return;
    api.get(`/api/users/${userId}/resumes`).catch(() => ({ data: [] }))
      .then(res => { setResumes(res.data || []); if (res.data?.length) setSelected(res.data[0].id); });
  }, [userId]);

  const handleAnalyze = async () => {
    if (!selected) return;
    setLoading(true);
    try {
      const { data } = await api.post(`/api/resumes/${selected}/improvements`, null, { params: { target_titles: JSON.stringify(['Python Developer', 'AI Engineer', 'ML Engineer']) } });
      setImp(data);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-charcoal-50 mb-2">Resume Improvements</h1>
      <p className="text-gray-600 dark:text-charcoal-400 mb-8">AI suggestions to optimize your resume</p>

      <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow p-5 mb-6">
        <div className="flex gap-3">
          <select value={selected || ''} onChange={e => setSelected(parseInt(e.target.value))} className="flex-1 border border-gray-300 dark:border-charcoal-600 bg-white dark:bg-charcoal-800 text-gray-900 dark:text-charcoal-100 rounded-md px-3 py-2.5 text-sm focus:ring-primary-500 focus:border-primary-500">
            <option value="">Select resume...</option>
            {resumes.map(r => <option key={r.id} value={r.id}>{r.filename}</option>)}
          </select>
          <button onClick={handleAnalyze} disabled={!selected || loading} className="px-6 py-2.5 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 text-sm font-medium">{loading ? 'Analyzing...' : 'Get Suggestions'}</button>
        </div>
      </div>

      {imp && (
        <div className="space-y-6">
          {imp.suggestions && (
            <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-charcoal-700"><h3 className="text-lg font-semibold text-gray-900 dark:text-charcoal-50">Improvement Tips</h3></div>
              <div className="p-6 space-y-3">{imp.suggestions.map((s, i) => (
                <div key={i} className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-charcoal-800 rounded-lg">
                  <span className="w-6 h-6 bg-primary-600 text-white rounded-full text-xs flex items-center justify-center flex-shrink-0">{i + 1}</span>
                  <p className="text-sm text-gray-700 dark:text-charcoal-300">{s}</p>
                </div>
              ))}</div>
            </div>
          )}
          {imp.missing_keywords?.length > 0 && (
            <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-charcoal-700"><h3 className="text-lg font-semibold text-gray-900 dark:text-charcoal-50">Missing Keywords</h3></div>
              <div className="p-6 flex flex-wrap gap-2">{imp.missing_keywords.map((k, i) => <span key={i} className="px-3 py-1 bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300 rounded-full text-sm">{k}</span>)}</div>
            </div>
          )}
          {imp.trending_skills?.length > 0 && (
            <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-charcoal-700"><h3 className="text-lg font-semibold text-gray-900 dark:text-charcoal-50">Trending Skills</h3></div>
              <div className="p-6 flex flex-wrap gap-2">{imp.trending_skills.map((s, i) => <span key={i} className="px-3 py-1 bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300 rounded-full text-sm">{s}</span>)}</div>
            </div>
          )}
          {imp.recommended_certifications?.length > 0 && (
            <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-charcoal-700"><h3 className="text-lg font-semibold text-gray-900 dark:text-charcoal-50">Recommended Certifications</h3></div>
              <div className="p-6 space-y-2">{imp.recommended_certifications.map((c, i) => <div key={i} className="text-gray-700 dark:text-charcoal-300 text-sm">✓ {c}</div>)}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
