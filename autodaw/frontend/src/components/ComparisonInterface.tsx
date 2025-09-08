import React, { useState, useEffect } from 'react';
import { Volume2, ArrowRight } from 'lucide-react';
import { comparisonAPI, audioAPI, Comparison } from '../services/api';

const ComparisonInterface: React.FC = () => {
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedOption, setSelectedOption] = useState<'a' | 'b' | null>(null);
  const [confidence, setConfidence] = useState(0.5);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // No audio state needed - HTML5 controls handle everything

  useEffect(() => {
    loadNextComparison();
  }, []);

  const loadNextComparison = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await comparisonAPI.getNext();

      if (result.comparison) {
        setComparison(result.comparison);
        // Reset form state
        setSelectedOption(null);
        setConfidence(0.5);
        setNotes('');
      } else {
        setComparison(null);
        setError(result.message || 'No pending comparisons available');
      }
    } catch (err) {
      setError('Failed to load comparison');
      console.error('Error loading comparison:', err);
    } finally {
      setLoading(false);
    }
  };

    // No custom audio handlers needed - HTML5 controls handle everything

  const handleOptionSelect = (option: 'a' | 'b') => {
    setSelectedOption(option);
  };

  const handleSubmitPreference = async () => {
    if (!comparison || !selectedOption) return;

    try {
      setSubmitting(true);
      await comparisonAPI.submitPreference(
        comparison.comparison_id,
        selectedOption,
        confidence,
        notes || undefined
      );

      // Load next comparison
      await loadNextComparison();
    } catch (err) {
      setError('Failed to submit preference');
      console.error('Error submitting preference:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const formatParameters = (params: any) => {
    if (!params) return 'N/A';
    return `Octave: ${params.octave?.toFixed(2) || 'N/A'}, Fine: ${params.fine_tuning?.toFixed(3) || 'N/A'}`;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading comparison...</p>
        </div>
      </div>
    );
  }

  if (error && !comparison) {
    return (
      <div className="text-center py-12">
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 max-w-md mx-auto">
          <p className="text-sm text-yellow-600">{error}</p>
          <button
            onClick={loadNextComparison}
            className="mt-4 px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!comparison) {
    return (
      <div className="text-center py-12">
        <Volume2 size={48} className="mx-auto mb-4 text-gray-300" />
        <p className="text-gray-500">No comparisons available</p>
        <button
          onClick={loadNextComparison}
          className="mt-4 px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
        >
          Check for New Comparisons
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900">Audio Comparison</h2>
        <p className="mt-2 text-gray-600">Listen to both options and select your preference</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Option A */}
        <div
          className={`bg-white rounded-lg shadow-md p-6 cursor-pointer border-2 transition-colors ${
            selectedOption === 'a'
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-gray-300'
          }`}
          onClick={() => handleOptionSelect('a')}
        >
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Option A</h3>
          </div>

          <div className="space-y-2 text-sm text-gray-600">
            <p><strong>Parameters:</strong> {formatParameters(comparison.solution_a.parameters)}</p>
            {comparison.solution_a.audio_file && (
              <p><strong>File:</strong> {comparison.solution_a.audio_file.filename}</p>
            )}
          </div>

          {comparison.solution_a.audio_file && (
            <div className="mt-4">
              <audio
                controls
                preload="metadata"
                className="w-full"
              >
                <source
                  src={audioAPI.getStreamUrl(comparison.solution_a.audio_file.id)}
                  type="audio/wav"
                />
                Your browser does not support audio playback.
              </audio>
            </div>
          )}
        </div>

        {/* Option B */}
        <div
          className={`bg-white rounded-lg shadow-md p-6 cursor-pointer border-2 transition-colors ${
            selectedOption === 'b'
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-gray-300'
          }`}
          onClick={() => handleOptionSelect('b')}
        >
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Option B</h3>
          </div>

          <div className="space-y-2 text-sm text-gray-600">
            <p><strong>Parameters:</strong> {formatParameters(comparison.solution_b.parameters)}</p>
            {comparison.solution_b.audio_file && (
              <p><strong>File:</strong> {comparison.solution_b.audio_file.filename}</p>
            )}
          </div>

          {comparison.solution_b.audio_file && (
            <div className="mt-4">
              <audio
                controls
                preload="metadata"
                className="w-full"
              >
                <source
                  src={audioAPI.getStreamUrl(comparison.solution_b.audio_file.id)}
                  type="audio/wav"
                />
                Your browser does not support audio playback.
              </audio>
            </div>
          )}
        </div>
      </div>

      {/* Preference submission form */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Submit Your Preference</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Confidence Level: {(confidence * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={confidence}
              onChange={(e) => setConfidence(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Not confident</span>
              <span>Very confident</span>
            </div>
          </div>

          <div>
            <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-2">
              Notes (optional)
            </label>
            <textarea
              id="notes"
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="Any additional comments about your preference..."
            />
          </div>

          <div className="flex justify-end">
            <button
              onClick={handleSubmitPreference}
              disabled={!selectedOption || submitting}
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Submitting...
                </>
              ) : (
                <>
                  Submit Preference
                  <ArrowRight size={16} className="ml-2" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComparisonInterface;
