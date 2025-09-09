import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause } from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

function App() {
  const [currentComparison, setCurrentComparison] = useState(null);
  const [selectedOption, setSelectedOption] = useState(null);
  const [confidence, setConfidence] = useState(50);
  const [notes, setNotes] = useState('');
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [playingAudio, setPlayingAudio] = useState(null);

  const audioRefA = useRef(null);
  const audioRefB = useRef(null);

  useEffect(() => {
    loadNextComparison();
    loadStats();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const loadNextComparison = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_BASE}/comparisons/next`);
      setCurrentComparison(response.data);
      resetForm();
    } catch (err) {
      setError('Failed to load next comparison');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/stats`);
      setStats(response.data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const resetForm = () => {
    setSelectedOption(null);
    setConfidence(50);
    setNotes('');
    setSuccess(null);
    stopAllAudio();
  };

  const stopAllAudio = () => {
    if (audioRefA.current) {
      audioRefA.current.pause();
      audioRefA.current.currentTime = 0;
    }
    if (audioRefB.current) {
      audioRefB.current.pause();
      audioRefB.current.currentTime = 0;
    }
    setPlayingAudio(null);
  };

  const handlePlayAudio = (option) => {
    stopAllAudio();

    const audioRef = option === 'a' ? audioRefA : audioRefB;
    if (audioRef.current) {
      // Stub: In production, this would load actual audio from the API
      setPlayingAudio(option);
      // Simulate audio playback
      setTimeout(() => setPlayingAudio(null), 3000);
    }
  };

  const handleOptionSelect = (option) => {
    setSelectedOption(option);
    stopAllAudio();
  };

  const submitPreference = async () => {
    if (!selectedOption || !currentComparison) return;

    try {
      setLoading(true);
      await axios.post(`${API_BASE}/comparisons/${currentComparison.id}/preference`, {
        comparison_id: currentComparison.id,
        preference: selectedOption,
        confidence: confidence / 100,
        notes: notes || null
      });

      setSuccess('Preference recorded successfully');
      await loadStats();

      // Load next comparison after brief delay
      setTimeout(() => {
        loadNextComparison();
      }, 1500);

    } catch (err) {
      setError('Failed to submit preference');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !currentComparison) {
    return (
      <div className="container">
        <div className="loading">Loading comparison data...</div>
      </div>
    );
  }

  return (
    <div className="container">
      <header className="header">
        <h1>Audio Comparison Tool</h1>
        <p>Listen to each audio sample and select your preference</p>
      </header>

      {stats && (
        <div className="stats-panel">
          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-value">{stats.completed_comparisons}</div>
              <div className="stat-label">Completed</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{stats.remaining_comparisons}</div>
              <div className="stat-label">Remaining</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{stats.average_confidence}%</div>
              <div className="stat-label">Avg Confidence</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">
                {stats.preference_distribution.a} / {stats.preference_distribution.b}
              </div>
              <div className="stat-label">A / B Preferences</div>
            </div>
          </div>
        </div>
      )}

      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}

      {!currentComparison ? (
        <div className="no-comparisons">
          <h3>No more comparisons available</h3>
          <p>All audio pairs have been evaluated</p>
        </div>
      ) : (
        <div className="comparison-card">
          <div className="audio-pair">
            <div
              className={`audio-option ${selectedOption === 'a' ? 'selected' : ''}`}
              onClick={() => handleOptionSelect('a')}
            >
              <div className="audio-title">Option A</div>
              <div className="audio-info">{currentComparison.audio_a.filename}</div>
              <div className="audio-controls">
                <button
                  className="play-button"
                  onClick={(e) => {
                    e.stopPropagation();
                    handlePlayAudio('a');
                  }}
                  disabled={playingAudio === 'a'}
                >
                  {playingAudio === 'a' ? <Pause size={16} /> : <Play size={16} />}
                  {playingAudio === 'a' ? 'Playing...' : 'Play'}
                </button>
              </div>
              <div className="audio-info">
                Duration: {currentComparison.audio_a.duration || 'Unknown'}s
              </div>
              {/* Stub audio element */}
              <audio ref={audioRefA} style={{ display: 'none' }}>
                <source src="#" type="audio/wav" />
              </audio>
            </div>

            <div
              className={`audio-option ${selectedOption === 'b' ? 'selected' : ''}`}
              onClick={() => handleOptionSelect('b')}
            >
              <div className="audio-title">Option B</div>
              <div className="audio-info">{currentComparison.audio_b.filename}</div>
              <div className="audio-controls">
                <button
                  className="play-button"
                  onClick={(e) => {
                    e.stopPropagation();
                    handlePlayAudio('b');
                  }}
                  disabled={playingAudio === 'b'}
                >
                  {playingAudio === 'b' ? <Pause size={16} /> : <Play size={16} />}
                  {playingAudio === 'b' ? 'Playing...' : 'Play'}
                </button>
              </div>
              <div className="audio-info">
                Duration: {currentComparison.audio_b.duration || 'Unknown'}s
              </div>
              {/* Stub audio element */}
              <audio ref={audioRefB} style={{ display: 'none' }}>
                <source src="#" type="audio/wav" />
              </audio>
            </div>
          </div>

          <div className="preference-section">
            <div className="confidence-slider">
              <label>Confidence Level: {confidence}%</label>
              <input
                type="range"
                min="0"
                max="100"
                value={confidence}
                onChange={(e) => setConfidence(parseInt(e.target.value))}
              />
              <div className="confidence-value">
                {confidence < 30 ? 'Low' : confidence < 70 ? 'Medium' : 'High'} Confidence
              </div>
            </div>

            <textarea
              className="notes-input"
              placeholder="Optional notes about your preference..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />

            <button
              className="submit-button"
              onClick={submitPreference}
              disabled={!selectedOption || loading}
            >
              {loading ? 'Submitting...' : 'Submit Preference'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
