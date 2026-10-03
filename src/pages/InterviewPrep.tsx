import { useState, useEffect } from 'react';
import api from '../api';
import axios from 'axios';  // Keep for backwards compatibility

interface Job { id: number; title: string; company: string; description: string; }
interface Question { id: number; category: string; question: string; suggested_answer: string; }

export default function InterviewPrep({ userId }: { userId: number | null }) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(false);
  const [showAnswer, setShowAnswer] = useState<Record<number, boolean>>({});

  useEffect(() => {
    if (!userId) return;
    api.get(`/api/users/${userId}/jobs`).catch(() => ({ data: [] }))
      .then(res => setJobs(res.data || []));
  }, [userId]);

  useEffect(() => {
    if (selected) {
      api.get(`/api/jobs/${selected}/interview-questions`).catch(() => ({ data: [] }))
        .then(res => { setQuestions(res.data || []); setShowAnswer({}); });
    }
  }, [selected]);

  const handleGenerate = async () => {
    if (!selected) return;
    setLoading(true);
    try {
      const { data } = await api.post('/api/interview-questions/generate', { job_id: selected });
      setQuestions(data);
      setShowAnswer({});
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const categories = [...new Set(questions.map(q => q.category))];

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-charcoal-50 mb-2">Interview Prep</h1>
      <p className="text-gray-600 dark:text-charcoal-400 mb-8">AI-generated interview questions with suggested answers</p>

      <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow p-5 mb-6">
        <div className="flex gap-3">
          <select value={selected || ''} onChange={e => setSelected(parseInt(e.target.value))} className="flex-1 border border-gray-300 dark:border-charcoal-600 bg-white dark:bg-charcoal-800 text-gray-900 dark:text-charcoal-100 rounded-md px-3 py-2.5 text-sm">
            <option value="">Select a job...</option>
            {jobs.map(j => <option key={j.id} value={j.id}>{j.title} at {j.company}</option>)}
          </select>
          <button onClick={handleGenerate} disabled={!selected || loading} className="px-6 py-2.5 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 text-sm font-medium">
            {loading ? 'Generating...' : 'Generate Questions'}
          </button>
        </div>
      </div>

      {loading && (
        <div className="bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
            <p className="text-primary-700 dark:text-primary-300 font-medium">Generating interview questions...</p>
          </div>
        </div>
      )}

      {questions.length > 0 && (
        <div className="space-y-6">
          {categories.map(cat => (
            <div key={cat} className="bg-white dark:bg-charcoal-900 rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-charcoal-700">
                <h3 className="font-semibold text-gray-900 dark:text-charcoal-50 capitalize">{cat} Questions</h3>
              </div>
              <div className="divide-y divide-gray-100 dark:divide-charcoal-700">
                {questions.filter(q => q.category === cat).map((q, i) => (
                  <div key={q.id} className="p-5">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <span className="text-xs text-gray-500 dark:text-charcoal-400">Q{i + 1}</span>
                        <p className="text-sm font-medium text-gray-900 dark:text-charcoal-50 mt-1">{q.question}</p>
                      </div>
                      {q.suggested_answer && (
                        <button onClick={() => setShowAnswer(prev => ({ ...prev, [q.id]: !prev[q.id] }))}
                          className="px-3 py-1 text-xs border border-gray-300 dark:border-charcoal-600 rounded hover:bg-gray-50 dark:hover:bg-charcoal-800 text-gray-600 dark:text-charcoal-300 flex-shrink-0">
                          {showAnswer[q.id] ? 'Hide' : 'Show'} Answer
                        </button>
                      )}
                    </div>
                    {showAnswer[q.id] && q.suggested_answer && (
                      <div className="mt-3 p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg text-sm text-emerald-800 dark:text-emerald-300">
                        {q.suggested_answer}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
