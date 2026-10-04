import React, { useState } from 'react';
import { TriangleAlert, Bug, ShieldAlert, Code2 } from 'lucide-react';
import './index.css';

const CodeSnippet = ({ context }) => {
  if (!context || !context.lines || context.lines.length === 0) {
    return <div className="finding-meta" style={{ marginTop: '10px', color: 'var(--color-gray)' }}>&gt; Source code unavailable</div>;
  }
  
  return (
    <div className="code-snippet-container">
      {context.lines.map((line) => (
        <div key={line.number} className={`code-line ${line.highlight ? 'highlight' : ''}`}>
          <div className="code-line-number">{line.number}</div>
          <div className="code-line-content">{line.code}</div>
        </div>
      ))}
    </div>
  );
};

const FindingCard = ({ finding, isSecurity }) => {
  const category = isSecurity ? 'SECURITY' : finding.category || 'CODE ISSUE';
  const title = isSecurity ? finding.issue : finding.message;
  const severity = (finding.severity || 'MEDIUM').toLowerCase();
  
  return (
    <div className="finding-card">
      <div className="finding-card-header">
        <div className="finding-title-group">
          <div className="finding-category">
            {isSecurity ? <ShieldAlert size={10} style={{marginRight: '4px', verticalAlign: 'middle'}}/> : <Bug size={10} style={{marginRight: '4px', verticalAlign: 'middle'}}/>}
            {category}
          </div>
          <div className="finding-title">{title}</div>
        </div>
        <div className={`finding-badge retro-font ${severity}`}>
          {severity.toUpperCase()}
        </div>
      </div>
      
      <div className="finding-meta">
        <div className="finding-meta-item">
          <Code2 size={12} style={{marginRight: '4px', verticalAlign: 'middle'}}/>
          {finding.file}
        </div>
        {finding.line && (
          <div className="finding-meta-item">
            LINE {finding.line}
          </div>
        )}
      </div>
      
      {finding.suggestion && (
        <div className="finding-desc">
          <span style={{ color: 'var(--color-cyan)' }}>Suggestion:</span> {finding.suggestion}
        </div>
      )}
      
      <CodeSnippet context={finding.code_context} />
    </div>
  );
};

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
        } catch (e) { }
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
          <span className="brand-text">REPOLENS<br />ARCADE SECURITY SCANNER </span>
        </div>
        <div className="nav-buttons">
        </div>
        <div className="top-bar-right">
          <span>USERNAME<br />999_</span>
          <div className="avatar"></div>
        </div>
      </header>

      <main className="main-content">
        <div className="title-area">
          <h1 className="main-title">
            <span className="text-cyan">REPO</span>
            <span className="text-magenta">LENS</span>
          </h1>
          <div className="subtitle blink">INSERT REPO LINK TO SCAN REPOSITORY</div>
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
                  <div className="warning-text retro-font" style={{ marginTop: '34px' }}>SECURITY VULNERABILITIES FOUND</div>
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
                <div className="log-text" style={{ whiteSpace: 'pre-wrap', fontSize: '1rem', lineHeight: '1.4', color: 'var(--color-gray)' }}>
                  {result.ai_summary}
                </div>
              </div>
            )}

            {/* Findings Cards */}
            <div className="findings-section">
              {result.issues.length > 0 && (
                <>
                  <div className="log-header" style={{ marginTop: '20px' }}>
                    <div className="log-title retro-font" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Bug size={16} /> CODE ISSUES
                    </div>
                  </div>
                  <div className="findings-grid">
                    {result.issues.map((issue, idx) => (
                      <FindingCard key={`issue-${idx}`} finding={issue} isSecurity={false} />
                    ))}
                  </div>
                </>
              )}
              
              {result.security.length > 0 && (
                <>
                  <div className="log-header" style={{ marginTop: '20px' }}>
                    <div className="log-title retro-font" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <ShieldAlert size={16} /> SECURITY VULNERABILITIES
                    </div>
                  </div>
                  <div className="findings-grid">
                    {result.security.map((sec, idx) => (
                      <FindingCard key={`sec-${idx}`} finding={sec} isSecurity={true} />
                    ))}
                  </div>
                </>
              )}
            </div>

          </div>
        )}
      </main>

      <footer className="footer retro-font">
        <div>&copy; 2026 REPOLENS</div>
        <div className="blink">PRESS START TO CONTINUE </div>
      </footer>
    </div>
  );
}

export default App;
