import React, { useState, useEffect } from 'react';
import './App.css';

/**
 * API_URL is injected at container runtime via docker-entrypoint.sh,
 * which writes /env-config.js exposing window._env_.
 * Falls back to REACT_APP_API_URL for local dev (set in .env.local).
 */
const API_URL = (window._env_ && window._env_.API_URL) || process.env.REACT_APP_API_URL || '';

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = () => {
    if (!API_URL) {
      setError('API_URL is not configured. Set it via the API_URL environment variable in Docker Compose.');
      return;
    }
    setLoading(true);
    setError(null);
    fetch(API_URL)
      .then((res) => {
        if (!res.ok) throw new Error('HTTP ' + res.status + ': ' + res.statusText);
        return res.json();
      })
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1>React API Client</h1>
        <p className="endpoint-label">
          Endpoint: <code>{API_URL || '(not set)'}</code>
        </p>
      </header>
      <main className="app-main">
        <button className="refresh-btn" onClick={fetchData} disabled={loading}>
          {loading ? 'Loading...' : 'Refresh'}
        </button>
        {loading && <p className="status">Fetching data...</p>}
        {error && (
          <div className="card error">
            <h2>Error</h2>
            <p>{error}</p>
          </div>
        )}
        {data && !error && (
          <div className="card success">
            <h2>Response</h2>
            {data.env && (
              <p className="env-tag">Environment: <strong>{data.env}</strong></p>
            )}
            <pre>{JSON.stringify(data, null, 2)}</pre>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
