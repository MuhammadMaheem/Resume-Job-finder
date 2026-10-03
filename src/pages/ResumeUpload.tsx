import { useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import api from '../api';
import axios from 'axios';  // Keep for backwards compatibility

interface ResumeUploadProps {
  userId: number | null;
}

export default function ResumeUpload({ userId }: ResumeUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [error, setError] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [resumeId, setResumeId] = useState<number | null>(null);
  const [showManualProfile, setShowManualProfile] = useState(false);
  const [additionalSkills, setAdditionalSkills] = useState('');
  const [educationDetails, setEducationDetails] = useState('');
  const [experienceDetails, setExperienceDetails] = useState('');
  const [certifications, setCertifications] = useState('');
  const [languages, setLanguages] = useState('');
  const [careerObjective, setCareerObjective] = useState('');
  const [githubUrl, setGithubUrl] = useState('');
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [otherNotes, setOtherNotes] = useState('');

  const onDrop = (acceptedFiles: File[]) => {
    if (acceptedFiles[0]) setSelectedFile(acceptedFiles[0]);
  };
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] } as any,
    multiple: false,
  } as any);

  useEffect(() => {
    if (analysis) {
      if (analysis.skills?.length) setAdditionalSkills(analysis.skills.join(', '));
      if (analysis.education?.length)
        setEducationDetails(
          analysis.education
            .map((e: any) => `${e.degree || ''} ${e.field || ''} at ${e.institution}`)
            .join('\n')
        );
      if (analysis.experience?.length)
        setExperienceDetails(
          analysis.experience
            .map((e: any) => `${e.title} at ${e.company} (${e.duration})`)
            .join('\n')
        );
      if (analysis.certifications?.length) setCertifications(analysis.certifications.join(', '));
      if (analysis.summary) setCareerObjective(analysis.summary);
    }
  }, [analysis]);

  const handleUpload = async () => {
    if (!userId || !selectedFile) return;
    setUploading(true);
    setError('');
    const formData = new FormData();
    formData.append('file', selectedFile);
    try {
      const { data } = await api.post(`/api/resumes/upload`, formData);
      setResumeId(data.id);
      setAnalysis(data.analysis);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleSaveProfile = async () => {
    if (!resumeId) return;
    setUploading(true);
    try {
      const profile = {
        additional_skills: additionalSkills
          .split(',')
          .map((s: string) => s.trim())
          .filter(Boolean),
        projects: [],
        education_details: educationDetails,
        experience_details: experienceDetails,
        certifications: certifications
          .split(',')
          .map((s: string) => s.trim())
          .filter(Boolean),
        languages: languages
          .split(',')
          .map((s: string) => s.trim())
          .filter(Boolean),
        preferred_job_titles: [],
        preferred_locations: [],
        preferred_job_type: 'Remote',
        career_objective: careerObjective,
        github_url: githubUrl,
        linkedin_url: linkedinUrl,
        portfolio_url: '',
        other_notes: otherNotes,
      };
      const { data } = await api.put(`/api/resumes/${resumeId}/profile`, profile);
      setAnalysis(data.analysis);
      setShowManualProfile(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-charcoal-50 mb-2">
        Resume Analysis
      </h1>
      <p className="text-gray-600 dark:text-charcoal-400 mb-8">
        Upload your PDF resume for AI-powered analysis
      </p>

      {!analysis && (
        <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow p-8">
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${isDragActive ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' : 'border-gray-300 dark:border-charcoal-600 hover:border-primary-400 hover:bg-gray-50 dark:hover:bg-charcoal-800'}`}
          >
            <input {...getInputProps()} />
            <div className="text-5xl mb-3">📄</div>
            <p className="text-lg text-gray-700 dark:text-charcoal-300">
              {isDragActive
                ? 'Drop your resume here'
                : selectedFile
                  ? `Selected: ${selectedFile.name}`
                  : 'Drag & drop your PDF resume here'}
            </p>
            <p className="text-sm text-gray-500 dark:text-charcoal-400 mt-1">or click to browse</p>
          </div>
          {selectedFile && (
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="mt-4 w-full bg-primary-600 text-white py-3 rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50"
            >
              {uploading ? 'Analyzing...' : 'Analyze Resume'}
            </button>
          )}
          {error && (
            <div className="mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-red-700 dark:text-red-400 text-sm">
              {error}
            </div>
          )}
        </div>
      )}

      {analysis && (
        <div className="space-y-6">
          <div className="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg p-4">
            <p className="text-emerald-900 dark:text-emerald-300 font-medium">
              ✅ Resume analyzed — {analysis.skills?.length || 0} skills detected
            </p>
          </div>

          <div className="grid grid-cols-4 gap-4">
            {[
              {
                label: 'Skills',
                val: analysis.skills?.length || 0,
                c: 'text-primary-600 dark:text-primary-400',
              },
              {
                label: 'Seniority',
                val: analysis.seniority_level || '—',
                c: 'text-primary-600 dark:text-primary-400',
              },
              {
                label: 'Experience',
                val: `${analysis.years_of_experience || '—'} yrs`,
                c: 'text-primary-600 dark:text-primary-400',
              },
              {
                label: 'Industries',
                val: analysis.industries?.length || 0,
                c: 'text-primary-600 dark:text-primary-400',
              },
            ].map((s, i) => (
              <div key={i} className="bg-white dark:bg-charcoal-900 rounded-lg shadow p-5">
                <div className="text-sm text-gray-500 dark:text-charcoal-400">{s.label}</div>
                <div className={`text-2xl font-bold capitalize ${s.c}`}>{s.val}</div>
              </div>
            ))}
          </div>

          <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-charcoal-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-charcoal-50">
                Detected Skills ({analysis.skills?.length || 0})
              </h3>
            </div>
            <div className="p-6">
              <div className="flex flex-wrap gap-2">
                {analysis.skills && analysis.skills.length > 0 ? (
                  analysis.skills.map((skill: string, idx: number) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-primary-100 dark:bg-primary-900/40 text-primary-800 dark:text-primary-300 rounded-full text-sm"
                    >
                      {skill}
                    </span>
                  ))
                ) : (
                  <p className="text-gray-500 dark:text-charcoal-400 text-sm">
                    No skills detected. Add them manually below.
                  </p>
                )}
              </div>
            </div>
          </div>

          {analysis.experience && analysis.experience.length > 0 && (
            <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-charcoal-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-charcoal-50">
                  Experience
                </h3>
              </div>
              <div className="p-6 space-y-3">
                {analysis.experience.map((exp: any, idx: number) => (
                  <div key={idx} className="border-l-4 border-primary-500 pl-4">
                    <div className="font-medium text-gray-900 dark:text-charcoal-50">
                      {exp.title}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-charcoal-400">
                      {exp.company} · {exp.duration || 'N/A'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {analysis.education && analysis.education.length > 0 && (
            <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-charcoal-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-charcoal-50">
                  Education
                </h3>
              </div>
              <div className="p-6 space-y-2">
                {analysis.education.map((edu: any, idx: number) => (
                  <div key={idx} className="text-gray-900 dark:text-charcoal-300">
                    <span className="font-medium">{edu.degree || edu.field}</span> —{' '}
                    {edu.institution}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={() => setShowManualProfile(!showManualProfile)}
              className="flex-1 py-3 border border-gray-300 dark:border-charcoal-600 text-gray-700 dark:text-charcoal-300 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-charcoal-800"
            >
              {showManualProfile ? 'Hide Editor' : '✏️ Edit & Add Details'}
            </button>
            <a
              href={`/api/resumes/${resumeId}/export-pdf`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 py-3 bg-emerald-600 text-white rounded-lg font-medium text-center hover:bg-emerald-700"
            >
              📄 Export PDF
            </a>
            <a
              href="/jobs"
              className="flex-1 py-3 bg-primary-600 text-white rounded-lg font-medium text-center hover:bg-primary-700"
            >
              🔍 Find Jobs →
            </a>
          </div>

          {showManualProfile && (
            <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-charcoal-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-charcoal-50">
                  Edit Profile Details
                </h3>
                <p className="text-sm text-gray-500 dark:text-charcoal-400 mt-1">
                  Pre-filled from your resume — edit or add more
                </p>
              </div>
              <div className="p-6 space-y-4">
                {[
                  {
                    label: 'Career Objective',
                    val: careerObjective,
                    set: setCareerObjective,
                    rows: 2,
                    type: 'textarea',
                  },
                  {
                    label: 'Skills (pre-filled — edit or add more)',
                    val: additionalSkills,
                    set: setAdditionalSkills,
                    rows: 3,
                    type: 'textarea',
                  },
                  {
                    label: 'Education (pre-filled)',
                    val: educationDetails,
                    set: setEducationDetails,
                    rows: 2,
                    type: 'textarea',
                  },
                  {
                    label: 'Experience (pre-filled)',
                    val: experienceDetails,
                    set: setExperienceDetails,
                    rows: 3,
                    type: 'textarea',
                  },
                ].map((f, i) => (
                  <div key={i}>
                    <label className="block text-sm font-medium text-gray-700 dark:text-charcoal-300 mb-1">
                      {f.label}
                    </label>
                    {f.type === 'textarea' ? (
                      <textarea
                        value={f.val as string}
                        onChange={(e) => f.set(e.target.value)}
                        rows={f.rows}
                        className="w-full border border-gray-300 dark:border-charcoal-600 bg-white dark:bg-charcoal-800 text-gray-900 dark:text-charcoal-100 rounded-md px-3 py-2 text-sm focus:ring-primary-500 focus:border-primary-500"
                      />
                    ) : (
                      <input
                        type="text"
                        value={f.val as string}
                        onChange={(e) => f.set(e.target.value)}
                        className="w-full border border-gray-300 dark:border-charcoal-600 bg-white dark:bg-charcoal-800 text-gray-900 dark:text-charcoal-100 rounded-md px-3 py-2 text-sm focus:ring-primary-500 focus:border-primary-500"
                      />
                    )}
                  </div>
                ))}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-charcoal-300 mb-1">
                      Certifications
                    </label>
                    <input
                      type="text"
                      value={certifications}
                      onChange={(e) => setCertifications(e.target.value)}
                      className="w-full border border-gray-300 dark:border-charcoal-600 bg-white dark:bg-charcoal-800 text-gray-900 dark:text-charcoal-100 rounded-md px-3 py-2 text-sm focus:ring-primary-500 focus:border-primary-500"
                      placeholder="AWS, GCP..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-charcoal-300 mb-1">
                      Languages
                    </label>
                    <input
                      type="text"
                      value={languages}
                      onChange={(e) => setLanguages(e.target.value)}
                      className="w-full border border-gray-300 dark:border-charcoal-600 bg-white dark:bg-charcoal-800 text-gray-900 dark:text-charcoal-100 rounded-md px-3 py-2 text-sm focus:ring-primary-500 focus:border-primary-500"
                      placeholder="English, Urdu..."
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-charcoal-300 mb-1">
                      GitHub
                    </label>
                    <input
                      type="text"
                      value={githubUrl}
                      onChange={(e) => setGithubUrl(e.target.value)}
                      className="w-full border border-gray-300 dark:border-charcoal-600 bg-white dark:bg-charcoal-800 text-gray-900 dark:text-charcoal-100 rounded-md px-3 py-2 text-sm focus:ring-primary-500 focus:border-primary-500"
                      placeholder="https://github.com/..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-charcoal-300 mb-1">
                      LinkedIn
                    </label>
                    <input
                      type="text"
                      value={linkedinUrl}
                      onChange={(e) => setLinkedinUrl(e.target.value)}
                      className="w-full border border-gray-300 dark:border-charcoal-600 bg-white dark:bg-charcoal-800 text-gray-900 dark:text-charcoal-100 rounded-md px-3 py-2 text-sm focus:ring-primary-500 focus:border-primary-500"
                      placeholder="https://linkedin.com/in/..."
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-charcoal-300 mb-1">
                    Other Notes
                  </label>
                  <textarea
                    value={otherNotes}
                    onChange={(e) => setOtherNotes(e.target.value)}
                    rows={2}
                    className="w-full border border-gray-300 dark:border-charcoal-600 bg-white dark:bg-charcoal-800 text-gray-900 dark:text-charcoal-100 rounded-md px-3 py-2 text-sm focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                <button
                  onClick={handleSaveProfile}
                  disabled={uploading}
                  className="w-full bg-primary-600 text-white py-3 rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50"
                >
                  {uploading ? 'Saving...' : 'Save & Re-analyze'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
