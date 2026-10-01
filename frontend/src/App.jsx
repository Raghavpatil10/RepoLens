import React, { useState } from 'react';
import { TriangleAlert, Bug, ShieldAlert } from 'lucide-react';
import './index.css';

function App() {
  const [repoUrl, setRepoUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleAnalyze = async () => {
    if (!repoUrl) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('http://127.0.0.1:8000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ repo_url: repoUrl }),
      });

      if (!response.ok) {
        let errMessage = 'Analysis failed';
        try {
          const errData = await response.json();
          if (errData.detail) errMessage = errData.detail;
        } catch (e) {}
        throw new Error(errMessage);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="top-bar">
        <div className="top-bar-left">
          <div className="logo-icon"></div>
          <span className="brand-text">REPOGUARD<br/>ARCADE SECURITY SCANNER v1.0</span>
        </div>
        <div className="nav-buttons">
          <button className="nav-btn active">SCAN</button>
          <button className="nav-btn">REPORTS</button>
          <button className="nav-btn">SETTINGS</button>
        </div>
        <div className="top-bar-right">
          <span>CREDITS<br/>999_</span>
          <div className="avatar"></div>
        </div>
      </header>

      <main className="main-content">
        <div className="title-area">
          <h1 className="main-title">
            <span className="text-cyan">GIT</span>
            <span className="text-magenta">ARCADE</span>
          </h1>
          <div className="subtitle blink">INSERT COIN TO SCAN REPOSITORY</div>
        </div>

        <div className="search-container">
          <input 
            type="text" 
            className="search-input" 
            placeholder="Enter GitHub Repository URL..." 
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
            disabled={loading}
          />
          <button className="search-btn glitch-hover" onClick={handleAnalyze} disabled={loading}>
            {loading ? 'ANALYZING...' : 'ANALYZE'}
          </button>
        </div>

        {error && <div className="error-message blink">ERROR: {error}</div>}

        {result && (
          <div className="dashboard-container">
            {/* Warning Cards */}
            <div className="panel">
              <div className="warning-cards">
                <div className="warning-card">
                  <TriangleAlert className="warning-icon" />
                  <div className="warning-text retro-font">CODE ISSUES DETECTED</div>
                  <div className="warning-number retro-font">{result.issues.length}</div>
                  <div className="warning-border"></div>
                </div>
                <div className="warning-card">
                  <div className="warning-text retro-font" style={{marginTop: '34px'}}>SECURITY VULNERABILITIES FOUND</div>
                  <div className="warning-number retro-font">{result.security.length}</div>
                  <div className="warning-border"></div>
                </div>
              </div>
            </div>

            {/* AI Summary (if any) */}
            {result.ai_summary && (
              <div className="panel">
                <div className="log-header">
                  <div className="log-title retro-font">AI SUMMARY</div>
                </div>
                <div className="log-text" style={{whiteSpace: 'pre-wrap', fontSize: '1rem', lineHeight: '1.4', color: 'var(--color-gray)'}}>
                  {result.ai_summary}
                </div>
              </div>
            )}

            {/* Code Issues */}
            {result.issues.length > 0 && (
              <div className="panel">
                <div className="log-header">
                  <div className="log-title retro-font" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Bug size={16} /> CODE ISSUES
                  </div>
                </div>
                <div className="log-list">
                  {result.issues.map((issue, idx) => (
                    <div key={`issue-${idx}`} className="log-item">
                      <div className="log-content">
                        <div className="log-text">{issue.message}</div>
                        <div className="log-meta">
                          {issue.file}{issue.line ? `:${issue.line}` : ''} &middot; Category: {issue.category}
                        </div>
                        {issue.suggestion && (
                          <div className="log-meta" style={{color: 'var(--color-cyan)', marginTop: '4px'}}>
                            Suggestion: {issue.suggestion}
                          </div>
                        )}
                      </div>
                      <div className={`log-status retro-font ${issue.severity?.toLowerCase() || 'medium'}`}>
                        {issue.severity || 'MEDIUM'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Security Vulnerabilities */}
            {result.security.length > 0 && (
              <div className="panel">
                <div className="log-header">
                  <div className="log-title retro-font" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <ShieldAlert size={16} /> SECURITY VULNERABILITIES
                  </div>
                </div>
                <div className="log-list">
                  {result.security.map((sec, idx) => (
                    <div key={`sec-${idx}`} className="log-item">
                      <div className="log-content">
                        <div className="log-text">{sec.issue}</div>
                        <div className="log-meta">
                          {sec.file}{sec.line ? `:${sec.line}` : ''} {sec.test_id ? `(${sec.test_id})` : ''}
                        </div>
                      </div>
                      <div className={`log-status retro-font ${sec.severity?.toLowerCase() || 'high'}`}>
                        {sec.severity || 'HIGH'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>
        )}
      </main>

      <footer className="footer retro-font">
        <div>&copy; 2026 REPOGUARD ARCADE</div>
        <div className="blink">PRESS START TO CONTINUE _</div>
      </footer>
    </div>
  );
}

export default App;
