import React, { useState, useEffect } from 'react';
import { Plus, Play, Settings, Clock } from 'lucide-react';
import { sessionAPI, populationAPI, Session } from '../services/api';

interface SessionManagerProps {
  currentSession: Session | null;
  onSessionSelect: (session: Session) => void;
}

const SessionManager: React.FC<SessionManagerProps> = ({ currentSession, onSessionSelect }) => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    target_frequency: 440.0,
    population_size: 8,
  });

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      setLoading(true);
      const sessionList = await sessionAPI.list();
      setSessions(sessionList);
      setError(null);
    } catch (err) {
      setError('Failed to load sessions');
      console.error('Error loading sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      const result = await sessionAPI.create(formData);

      // Reload sessions list
      await loadSessions();

      // Select the new session
      onSessionSelect(result.session);

      // Reset form
      setFormData({
        name: '',
        target_frequency: 440.0,
        population_size: 8,
      });
      setShowCreateForm(false);
      setError(null);
    } catch (err) {
      setError('Failed to create session');
      console.error('Error creating session:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInitializePopulation = async (session: Session) => {
    try {
      setLoading(true);
      await populationAPI.initialize(session.id);

      // Reload sessions to get updated generation count
      await loadSessions();
      setError(null);
    } catch (err) {
      setError('Failed to initialize population');
      console.error('Error initializing population:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">GA Optimization Sessions</h2>
        <button
          onClick={() => setShowCreateForm(true)}
          disabled={loading}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          <Plus size={16} className="mr-2" />
          New Session
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {showCreateForm && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Session</h3>
          <form onSubmit={handleCreateSession} className="space-y-4">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                Session Name
              </label>
              <input
                type="text"
                id="name"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="e.g., Frequency Optimization Test 1"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="target_frequency" className="block text-sm font-medium text-gray-700">
                  Target Frequency (Hz)
                </label>
                <input
                  type="number"
                  id="target_frequency"
                  step="0.1"
                  value={formData.target_frequency}
                  onChange={(e) => setFormData({ ...formData, target_frequency: parseFloat(e.target.value) })}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>

              <div>
                <label htmlFor="population_size" className="block text-sm font-medium text-gray-700">
                  Population Size
                </label>
                <input
                  type="number"
                  id="population_size"
                  min="4"
                  max="32"
                  value={formData.population_size}
                  onChange={(e) => setFormData({ ...formData, population_size: parseInt(e.target.value) })}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Session'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        {loading && sessions.length === 0 ? (
          <div className="p-4 text-center text-gray-500">Loading sessions...</div>
        ) : sessions.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            No sessions yet. Create your first optimization session to get started.
          </div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {sessions.map((session) => (
              <li key={session.id}>
                <div className="px-4 py-4 flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <div className={`w-2 h-2 rounded-full ${
                        session.status === 'active' ? 'bg-green-400' : 'bg-gray-400'
                      }`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {session.name}
                      </p>
                      <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                        <span>Target: {session.target_frequency}Hz</span>
                        <span>Population: {session.population_size}</span>
                        <span>Generation: {session.current_generation}</span>
                      </div>
                      <p className="mt-1 text-xs text-gray-400">
                        <Clock size={12} className="inline mr-1" />
                        Created {formatDate(session.created_at)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {session.current_generation === 0 && (
                      <button
                        onClick={() => handleInitializePopulation(session)}
                        disabled={loading}
                        className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
                      >
                        <Play size={12} className="mr-1" />
                        Initialize
                      </button>
                    )}
                    <button
                      onClick={() => onSessionSelect(session)}
                      className={`inline-flex items-center px-3 py-1 border text-xs font-medium rounded focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                        currentSession?.id === session.id
                          ? 'border-blue-600 text-blue-600 bg-blue-50 focus:ring-blue-500'
                          : 'border-gray-300 text-gray-700 bg-white hover:bg-gray-50 focus:ring-blue-500'
                      }`}
                    >
                      <Settings size={12} className="mr-1" />
                      {currentSession?.id === session.id ? 'Selected' : 'Select'}
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default SessionManager;
