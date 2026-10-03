import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import api from '../api';
import axios from 'axios';  // Keep for backwards compatibility

export default function Settings({ userId }: { userId: number | null }) {
  const [user, setUser] = useState<any>(null);
  const [email, setEmail] = useState('');
  const [enabled, setEnabled] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!userId) return;
    api.get(`/api/users/${userId}`).catch(() => ({ data: null }))
      .then(res => {
        if (res.data) {
          setUser(res.data);
          setEmail(res.data.notification_email || '');
          setEnabled(res.data.notification_enabled || false);
        }
      });
  }, [userId]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.patch(`/api/users/${userId}/notifications`, {
        notification_email: email,
        notification_enabled: enabled,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) { console.error(err); }
    finally { setSaving(false); }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-charcoal-50 mb-2">Settings</h1>
      <p className="text-gray-600 dark:text-charcoal-400 mb-8">Manage your account and notification preferences</p>

      {/* Notifications */}
      <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-charcoal-700"><h3 className="font-semibold text-gray-900 dark:text-charcoal-50">Email Notifications</h3></div>
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900 dark:text-charcoal-50">Enable Notifications</p>
              <p className="text-sm text-gray-500 dark:text-charcoal-400">Get notified about new matching jobs</p>
            </div>
            <button onClick={() => setEnabled(!enabled)} className={`w-12 h-6 rounded-full transition-colors ${enabled ? 'bg-primary-600' : 'bg-gray-300 dark:bg-charcoal-600'}`}>
              <div className={`w-5 h-5 bg-white rounded-full shadow transform transition-transform ${enabled ? 'translate-x-6' : 'translate-x-0.5'}`}></div>
            </button>
          </div>
          {enabled && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-charcoal-300 mb-1">Notification Email</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} className="w-full border border-gray-300 dark:border-charcoal-600 bg-white dark:bg-charcoal-800 text-gray-900 dark:text-charcoal-100 rounded-md px-3 py-2 text-sm" placeholder="your@email.com" />
            </div>
          )}
          <button onClick={handleSave} disabled={saving} className="px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 text-sm font-medium">
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
          {saved && <p className="text-sm text-emerald-600 dark:text-emerald-400">Settings saved!</p>}
        </div>
      </div>

      {/* Quick Links */}
      <div className="bg-white dark:bg-charcoal-900 rounded-lg shadow mt-6">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-charcoal-700"><h3 className="font-semibold text-gray-900 dark:text-charcoal-50">Quick Links</h3></div>
        <div className="p-6 space-y-3">
          <Link to="/resume" className="block p-3 bg-gray-50 dark:bg-charcoal-800 rounded-lg hover:bg-gray-100 dark:hover:bg-charcoal-700">
            <span className="font-medium text-gray-900 dark:text-charcoal-50">Upload Resume</span>
            <p className="text-sm text-gray-500 dark:text-charcoal-400">Add or update your resume</p>
          </Link>
          <Link to="/jobs" className="block p-3 bg-gray-50 dark:bg-charcoal-800 rounded-lg hover:bg-gray-100 dark:hover:bg-charcoal-700">
            <span className="font-medium text-gray-900 dark:text-charcoal-50">Find Jobs</span>
            <p className="text-sm text-gray-500 dark:text-charcoal-400">Search for matching positions</p>
          </Link>
          <Link to="/compare" className="block p-3 bg-gray-50 dark:bg-charcoal-800 rounded-lg hover:bg-gray-100 dark:hover:bg-charcoal-700">
            <span className="font-medium text-gray-900 dark:text-charcoal-50">Compare Resumes</span>
            <p className="text-sm text-gray-500 dark:text-charcoal-400">Side-by-side resume comparison</p>
          </Link>
        </div>
      </div>
    </div>
  );
}
