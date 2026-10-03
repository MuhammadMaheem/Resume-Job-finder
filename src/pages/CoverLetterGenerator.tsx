import { useState, useEffect } from 'react';
import api from '../api';
import axios from 'axios';  // Keep for backwards compatibility

interface Job { id: number; title: string; company: string; }

export default function CoverLetterGenerator({ userId }: { userId: number | null }) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [generating, setGenerating] = useState(false);
  const [letter, setLetter] = useState<string | null>(null);

  useEffect(() => {
    if (!userId) return;
    api.get(`/api/users/${userId}/jobs`).catch(() => ({ data: [] }))
      .then(res => setJobs(res.data || []));
  }, [userId]);

  const handleGenerate = async () => {
    if (!selected) return;
    setGenerating(true); setLetter(null);
    try { const { data } = await api.post('/api/cover-letters/generate', { job_id: selected }); setLetter(data.content); }
    catch (err) { console.error(err); }
    finally { setGenerating(false); }
  };

  const job = jobs.find(j => j.id === selected);

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-charcoal-50 mb-2">Cover Letter Generator</h1>
      <p className="text-gray-600 dark:text-charcoal-400 mb-8">AI-generated cover letters for each job</p>

      <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow p-5 mb-6">
        <div className="flex gap-3">
          <select value={selected || ''} onChange={e => setSelected(parseInt(e.target.value))} className="flex-1 border border-gray-300 dark:border-charcoal-600 bg-white dark:bg-charcoal-800 text-gray-900 dark:text-charcoal-100 rounded-md px-3 py-2.5 text-sm focus:ring-primary-500 focus:border-primary-500">
            <option value="">Select a job...</option>
            {jobs.map(j => <option key={j.id} value={j.id}>{j.title} at {j.company}</option>)}
          </select>
          <button onClick={handleGenerate} disabled={!selected || generating} className="px-6 py-2.5 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 text-sm font-medium">{generating ? 'Generating...' : 'Generate'}</button>
        </div>
      </div>

      {generating && (
        <div className="bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
            <p className="text-primary-700 dark:text-primary-300 font-medium">Writing your cover letter...</p>
          </div>
        </div>
      )}

      {letter && job && (
        <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-charcoal-700 flex justify-between items-center">
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-charcoal-50">Cover Letter</h3>
              <p className="text-sm text-gray-500 dark:text-charcoal-400">{job.title} at {job.company}</p>
            </div>
            <button onClick={() => navigator.clipboard.writeText(letter)} className="px-3 py-1.5 text-sm border border-gray-300 dark:border-charcoal-600 text-gray-700 dark:text-charcoal-300 rounded hover:bg-gray-50 dark:hover:bg-charcoal-800">📋 Copy</button>
          </div>
          <div className="p-6">
            <div className="whitespace-pre-wrap text-gray-700 dark:text-charcoal-300 leading-relaxed text-sm">{letter}</div>
          </div>
        </div>
      )}

      {!letter && !generating && jobs.length === 0 && (
        <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow p-12 text-center">
          <div className="text-5xl mb-4">✉️</div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-charcoal-50">No jobs available</h3>
          <p className="text-gray-500 dark:text-charcoal-400 mt-1">Search for jobs first to generate cover letters</p>
        </div>
      )}
    </div>
  );
}
