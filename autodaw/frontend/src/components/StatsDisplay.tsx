import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Clock, Users, RefreshCw } from 'lucide-react';
import { statsAPI, Stats } from '../services/api';

const StatsDisplay: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const statsData = await statsAPI.get();
      setStats(statsData);
    } catch (err) {
      setError('Failed to load statistics');
      console.error('Error loading stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const getCompletionPercentage = () => {
    if (!stats || stats.total_comparisons === 0) return 0;
    return Math.round((stats.completed_comparisons / stats.total_comparisons) * 100);
  };

  const getPreferencePercentage = (preference: string) => {
    if (!stats || !stats.preference_distribution) return 0;
    const total = Object.values(stats.preference_distribution).reduce((sum, count) => sum + count, 0);
    if (total === 0) return 0;
    return Math.round(((stats.preference_distribution[preference] || 0) / total) * 100);
  };

  if (loading && !stats) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading statistics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Optimization Statistics</h2>
        <button
          onClick={loadStats}
          disabled={loading}
          className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          <RefreshCw size={16} className={`mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {!stats ? (
        <div className="text-center py-12">
          <BarChart3 size={48} className="mx-auto mb-4 text-gray-300" />
          <p className="text-gray-500">No statistics available</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Total Comparisons */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Users className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Total Comparisons
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {stats.total_comparisons}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Completed Comparisons */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <TrendingUp className="h-6 w-6 text-green-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Completed
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {stats.completed_comparisons}
                      <span className="text-sm text-gray-500 ml-1">
                        ({getCompletionPercentage()}%)
                      </span>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Remaining Comparisons */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Clock className="h-6 w-6 text-yellow-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Remaining
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {stats.remaining_comparisons}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* Average Confidence */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <BarChart3 className="h-6 w-6 text-blue-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Avg Confidence
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {(stats.average_confidence * 100).toFixed(1)}%
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Progress Bar */}
      {stats && stats.total_comparisons > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Comparison Progress</h3>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
              style={{ width: `${getCompletionPercentage()}%` }}
            ></div>
          </div>
          <div className="mt-2 flex justify-between text-sm text-gray-600">
            <span>{stats.completed_comparisons} completed</span>
            <span>{stats.remaining_comparisons} remaining</span>
          </div>
        </div>
      )}

      {/* Preference Distribution */}
      {stats && Object.keys(stats.preference_distribution).length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Preference Distribution</h3>
          <div className="space-y-4">
            {Object.entries(stats.preference_distribution).map(([preference, count]) => (
              <div key={preference}>
                <div className="flex justify-between text-sm font-medium text-gray-700">
                  <span>Option {preference.toUpperCase()}</span>
                  <span>{count} votes ({getPreferencePercentage(preference)}%)</span>
                </div>
                <div className="mt-1 w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${
                      preference === 'a' ? 'bg-blue-500' : 'bg-green-500'
                    }`}
                    style={{ width: `${getPreferencePercentage(preference)}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Additional Insights */}
      {stats && stats.completed_comparisons > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Insights</h3>
          <div className="space-y-3 text-sm text-gray-600">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span>
                {stats.completed_comparisons} comparisons have been evaluated out of {stats.total_comparisons} total
              </span>
            </div>

            {stats.average_confidence > 0 && (
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span>
                  Average user confidence is {(stats.average_confidence * 100).toFixed(1)}%
                  {stats.average_confidence >= 0.7 ? ' (high confidence)' :
                   stats.average_confidence >= 0.5 ? ' (moderate confidence)' : ' (low confidence)'}
                </span>
              </div>
            )}

            {Object.keys(stats.preference_distribution).length === 2 && (
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                <span>
                  {Math.abs(getPreferencePercentage('a') - getPreferencePercentage('b')) < 10
                    ? 'Preferences are closely balanced between options'
                    : `Strong preference trend towards option ${
                        getPreferencePercentage('a') > getPreferencePercentage('b') ? 'A' : 'B'
                      }`}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default StatsDisplay;
