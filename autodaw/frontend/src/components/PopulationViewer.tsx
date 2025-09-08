import React, { useState, useEffect } from 'react';
import { Play, TrendingUp, TrendingDown, Volume2, RefreshCw } from 'lucide-react';
import { sessionAPI, populationAPI, Population, PopulationWithSolutions } from '../services/api';

interface PopulationViewerProps {
  sessionId: string;
}

const PopulationViewer: React.FC<PopulationViewerProps> = ({ sessionId }) => {
  const [populations, setPopulations] = useState<Population[]>([]);
  const [selectedPopulation, setSelectedPopulation] = useState<PopulationWithSolutions | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPopulations();
  }, [sessionId]);

  const loadPopulations = async () => {
    try {
      setLoading(true);
      setError(null);
      const pops = await sessionAPI.getPopulations(sessionId);
      setPopulations(pops);

      // Auto-select the latest population
      if (pops.length > 0 && !selectedPopulation) {
        loadPopulationDetails(pops[0].id);
      }
    } catch (err) {
      setError('Failed to load populations');
      console.error('Error loading populations:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadPopulationDetails = async (populationId: string) => {
    try {
      setLoading(true);
      const details = await populationAPI.get(populationId);
      setSelectedPopulation(details);
      setError(null);
    } catch (err) {
      setError('Failed to load population details');
      console.error('Error loading population details:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatParameters = (params: any) => {
    if (!params) return 'N/A';
    return `Oct: ${params.octave?.toFixed(2) || 'N/A'}, Fine: ${params.fine_tuning?.toFixed(3) || 'N/A'}`;
  };

  const formatBTStrength = (btStrength: any) => {
    if (!btStrength) return 'N/A';
    const strength = (btStrength.strength * 100).toFixed(1);
    return `${strength}%`;
  };

  const getBTStrengthColor = (btStrength: any) => {
    if (!btStrength) return 'text-gray-400';
    const strength = btStrength.strength;
    if (strength >= 0.7) return 'text-green-600';
    if (strength >= 0.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getBTIcon = (btStrength: any) => {
    if (!btStrength) return null;
    const strength = btStrength.strength;
    if (strength >= 0.5) return <TrendingUp size={16} />;
    return <TrendingDown size={16} />;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading && populations.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading populations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Population Browser</h2>
        <button
          onClick={loadPopulations}
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

      {populations.length === 0 ? (
        <div className="text-center py-12">
          <Volume2 size={48} className="mx-auto mb-4 text-gray-300" />
          <p className="text-gray-500">No populations found for this session</p>
          <p className="text-sm text-gray-400 mt-2">Initialize a population in the Sessions tab to get started</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Population List */}
          <div className="lg:col-span-1">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Generations</h3>
            <div className="space-y-2">
              {populations.map((pop) => (
                <button
                  key={pop.id}
                  onClick={() => loadPopulationDetails(pop.id)}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    selectedPopulation?.population_id === pop.id
                      ? 'border-blue-500 bg-blue-50 text-blue-900'
                      : 'border-gray-200 bg-white hover:bg-gray-50'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium">Generation {pop.generation}</p>
                      <p className="text-sm text-gray-500">{pop.solution_count} solutions</p>
                    </div>
                    <p className="text-xs text-gray-400">
                      {formatDate(pop.created_at)}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Population Details */}
          <div className="lg:col-span-2">
            {selectedPopulation ? (
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Solutions in Population {selectedPopulation.population_id.slice(-8)}
                </h3>

                {selectedPopulation.solutions.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    No solutions found in this population
                  </div>
                ) : (
                  <div className="space-y-3">
                    {selectedPopulation.solutions
                      .sort((a, b) => {
                        // Sort by BT strength first, then by rank
                        if (a.bt_strength && b.bt_strength) {
                          return b.bt_strength.strength - a.bt_strength.strength;
                        }
                        if (a.bt_strength && !b.bt_strength) return -1;
                        if (!a.bt_strength && b.bt_strength) return 1;
                        return (a.rank || 999) - (b.rank || 999);
                      })
                      .map((solution, index) => (
                        <div
                          key={solution.id}
                          className="bg-white border border-gray-200 rounded-lg p-4"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-4">
                                <div className="flex-shrink-0">
                                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                                    <span className="text-sm font-medium text-blue-800">
                                      {index + 1}
                                    </span>
                                  </div>
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm font-medium text-gray-900">
                                    {formatParameters(solution.parameters)}
                                  </p>
                                  <div className="mt-1 flex items-center space-x-4 text-xs text-gray-500">
                                    {solution.rank && (
                                      <span>Rank: {solution.rank}</span>
                                    )}
                                    {solution.fitness && (
                                      <span>Fitness: {solution.fitness.toFixed(4)}</span>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>

                            <div className="flex items-center space-x-3">
                              {/* Bradley-Terry Strength */}
                              <div className={`flex items-center space-x-1 ${getBTStrengthColor(solution.bt_strength)}`}>
                                {getBTIcon(solution.bt_strength)}
                                <span className="text-sm font-medium">
                                  {formatBTStrength(solution.bt_strength)}
                                </span>
                              </div>

                              {/* Audio Playback */}
                              {solution.audio_file_id && (
                                <button
                                  onClick={() => {
                                    const audio = new Audio(`/api/audio/${solution.audio_file_id}/stream`);
                                    audio.play().catch(console.error);
                                  }}
                                  className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                                  title="Play audio"
                                >
                                  <Play size={16} />
                                </button>
                              )}
                            </div>
                          </div>

                          {/* Confidence Interval */}
                          {solution.bt_strength?.confidence_interval_lower !== undefined &&
                           solution.bt_strength?.confidence_interval_upper !== undefined && (
                            <div className="mt-2 text-xs text-gray-400">
                              CI: [{(solution.bt_strength.confidence_interval_lower * 100).toFixed(1)}%, {(solution.bt_strength.confidence_interval_upper * 100).toFixed(1)}%]
                            </div>
                          )}
                        </div>
                      ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <Volume2 size={48} className="mx-auto mb-4 text-gray-300" />
                <p>Select a population to view its solutions</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default PopulationViewer;
