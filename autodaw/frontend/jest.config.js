module.exports = {
  preset: 'react-scripts',
  transformIgnorePatterns: [
    'node_modules/(?!(axios)/)'
  ],
  moduleNameMapper: {
    '^axios$': require.resolve('axios'),
  },
  testEnvironment: 'jsdom'
};
