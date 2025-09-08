import React, { useState, useEffect } from 'react';
import './App.css';
import SessionManager from './components/SessionManager';
import ComparisonInterface from './components/ComparisonInterface';
import PopulationViewer from './components/PopulationViewer';
import StatsDisplay from './components/StatsDisplay';
import { Session } from './services/api';
import { Settings, Activity, Users, BarChart3 } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState<'sessions' | 'comparisons' | 'populations' | 'stats'>('sessions');
  const [currentSession, setCurrentSession] = useState<Session | null>(null);

  const tabs = [
    { id: 'sessions' as const, label: 'Sessions', icon: Settings },
    { id: 'comparisons' as const, label: 'Comparisons', icon: Activity },
    { id: 'populations' as const, label: 'Populations', icon: Users },
    { id: 'stats' as const, label: 'Statistics', icon: BarChart3 }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">AutoDAW</h1>
              <span className="ml-2 text-sm text-gray-500">GA+JSI+Audio Oracle Optimization</span>
            </div>
            {currentSession && (
              <div className="text-sm text-gray-600">
                Session: <span className="font-medium">{currentSession.name}</span>
                {currentSession.target_frequency && (
                  <span className="ml-2">Target: {currentSession.target_frequency}Hz</span>
                )}
              </div>
            )}
          </div>
        </div>
      </header>

      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon size={16} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'sessions' && (
          <SessionManager
            currentSession={currentSession}
            onSessionSelect={setCurrentSession}
          />
        )}

        {activeTab === 'comparisons' && (
          <ComparisonInterface />
        )}

        {activeTab === 'populations' && currentSession && (
          <PopulationViewer sessionId={currentSession.id} />
        )}

        {activeTab === 'stats' && (
          <StatsDisplay />
        )}

        {activeTab === 'populations' && !currentSession && (
          <div className="text-center text-gray-500 py-12">
            <Users size={48} className="mx-auto mb-4 text-gray-300" />
            <p>Select a session first to view populations</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
