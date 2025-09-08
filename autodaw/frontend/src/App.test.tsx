import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

// Mock the API service to avoid axios import issues
jest.mock('./services/api', () => ({
  sessionAPI: {
    list: jest.fn().mockResolvedValue([]),
    create: jest.fn(),
    get: jest.fn(),
    getPopulations: jest.fn().mockResolvedValue([])
  },
  comparisonAPI: {
    getNext: jest.fn().mockResolvedValue({ comparison: null }),
    submitPreference: jest.fn()
  },
  statsAPI: {
    get: jest.fn().mockResolvedValue({
      total_comparisons: 0,
      completed_comparisons: 0,
      remaining_comparisons: 0,
      preference_distribution: {},
      average_confidence: 0
    })
  },
  populationAPI: {
    initialize: jest.fn(),
    get: jest.fn()
  }
}));

test('renders AutoDAW title', () => {
  render(<App />);
  const titleElement = screen.getByText(/AutoDAW/i);
  expect(titleElement).toBeInTheDocument();
});

test('renders navigation tabs', () => {
  render(<App />);

  expect(screen.getByText('Sessions')).toBeInTheDocument();
  expect(screen.getByText('Comparisons')).toBeInTheDocument();
  expect(screen.getByText('Populations')).toBeInTheDocument();
  expect(screen.getByText('Statistics')).toBeInTheDocument();
});
