import React, { useState, useEffect } from 'react';
import { Play, Activity, Clock, BarChart2, CheckCircle, ShieldAlert, FileSpreadsheet, RefreshCw, Cpu, Award } from 'lucide-react';

export default function AnalyticsPanel({ config, ollamaStatus }) {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [runMode, setRunMode] = useState('mock'); // Mode to execute evaluation

  const fetchAnalytics = () => {
    fetch('http://localhost:8000/api/analytics')
      .then((res) => res.json())
      .then((data) => {
        setAnalytics(data);
      })
      .catch((err) => console.error('Error fetching analytics:', err));
  };

  useEffect(() => {
    fetchAnalytics();
    // Poll analytics every 5 seconds to keep live session metrics current
    const interval = setInterval(fetchAnalytics, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleRunEvaluation = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mode: runMode,
          embedding_model: config.embeddingModel,
          llm_model: config.llmModel,
        }),
      });
      if (response.ok) {
        fetchAnalytics();
      }
    } catch (err) {
      console.error('Error running evaluation:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!analytics) {
    return (
      <div style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center' }}>
        <RefreshCw size={32} className="status-dot loading" style={{ animation: 'spin 2s linear infinite' }} />
      </div>
    );
  }

  const live = analytics.live_session;
  const latest = analytics.latest_evaluation;
  const history = analytics.evaluation_history || [];

  // Helper to render SVG progress/gauge bar
  const ProgressBar = ({ value, color = 'var(--accent-teal)' }) => {
    const percent = Math.min(Math.max(value * 100, 0), 100);
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', width: '100%' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
          <span style={{ color: 'var(--text-secondary)' }}>Accuracy Rate</span>
          <span style={{ color: '#fff', fontWeight: 600 }}>{percent.toFixed(0)}%</span>
        </div>
        <div style={{ height: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '99px', overflow: 'hidden', border: '1px solid var(--glass-border)' }}>
          <div style={{ height: '100%', width: `${percent}%`, background: color, borderRadius: '99px', transition: 'width 0.8s ease-in-out' }} />
        </div>
      </div>
    );
  };

  // Render SVG History Chart
  const renderHistoryChart = () => {
    if (history.length === 0) {
      return <div className="chart-fallback-text">No evaluation history found. Run benchmark evaluators to generate history chart.</div>;
    }

    const width = 680;
    const height = 180;
    const padding = 30;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;

    // Take max 10 points
    const dataPoints = history.slice(-10);
    const maxIndex = dataPoints.length - 1;

    // Get coordinates for values (Precision@1 and Recall@3)
    const getCoordinates = (index, value) => {
      const x = padding + (maxIndex > 0 ? (index / maxIndex) * chartWidth : chartWidth / 2);
      const y = padding + chartHeight - value * chartHeight;
      return { x, y };
    };

    // Build SVG path lines
    let p1Points = '';
    let r3Points = '';
    let mrrPoints = '';

    dataPoints.forEach((run, idx) => {
      const p1 = run.metrics.precision_at_1;
      const r3 = run.metrics.recall_at_3;
      const mrr = run.metrics.mrr;

      const p1Coords = getCoordinates(idx, p1);
      const r3Coords = getCoordinates(idx, r3);
      const mrrCoords = getCoordinates(idx, mrr);

      p1Points += `${idx === 0 ? 'M' : 'L'} ${p1Coords.x} ${p1Coords.y} `;
      r3Points += `${idx === 0 ? 'M' : 'L'} ${r3Coords.x} ${r3Coords.y} `;
      mrrPoints += `${idx === 0 ? 'M' : 'L'} ${mrrCoords.x} ${mrrCoords.y} `;
    });

    return (
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} style={{ overflow: 'visible' }}>
        {/* Grids */}
        {[0, 0.25, 0.5, 0.75, 1.0].map((v, i) => {
          const y = padding + chartHeight - v * chartHeight;
          return (
            <g key={i}>
              <line x1={padding} y1={y} x2={width - padding} y2={y} stroke="rgba(255, 255, 255, 0.05)" strokeDasharray="4 4" />
              <text x={padding - 8} y={y + 4} fill="var(--text-muted)" fontSize="9" textAnchor="end">{v * 100}%</text>
            </g>
          );
        })}

        {/* X Axis labels */}
        {dataPoints.map((run, idx) => {
          const x = padding + (maxIndex > 0 ? (idx / maxIndex) * chartWidth : chartWidth / 2);
          const timeStr = run.timestamp.split(' ')[1] || ''; // HH:MM:SS
          return (
            <g key={idx}>
              <text x={x} y={height - 8} fill="var(--text-muted)" fontSize="8" textAnchor="middle">{timeStr}</text>
              <text x={x} y={height} fill="var(--text-muted)" fontSize="8" textAnchor="middle">{run.engine_mode.toUpperCase()}</text>
            </g>
          );
        })}

        {/* Lines */}
        <path d={p1Points} fill="none" stroke="var(--accent-violet)" strokeWidth="2.5" strokeLinecap="round" />
        <path d={r3Points} fill="none" stroke="var(--accent-teal)" strokeWidth="2.5" strokeLinecap="round" />
        <path d={mrrPoints} fill="none" stroke="var(--accent-rose)" strokeWidth="1.5" strokeLinecap="round" strokeDasharray="3 3" />

        {/* Dots */}
        {dataPoints.map((run, idx) => {
          const p1 = run.metrics.precision_at_1;
          const r3 = run.metrics.recall_at_3;
          const p1Coords = getCoordinates(idx, p1);
          const r3Coords = getCoordinates(idx, r3);

          return (
            <g key={idx}>
              <circle cx={p1Coords.x} cy={p1Coords.y} r="4" fill="#0b0b0f" stroke="var(--accent-violet)" strokeWidth="2" />
              <circle cx={r3Coords.x} cy={r3Coords.y} r="4" fill="#0b0b0f" stroke="var(--accent-teal)" strokeWidth="2" />
            </g>
          );
        })}
      </svg>
    );
  };

  return (
    <div className="analytics-layout">
      {/* Top Banner Control Panel */}
      <div className="analytics-header-bar">
        <div className="analytics-title">
          <h2>RAG Benchmarks & Analytics</h2>
          <p>Analyze retrieval accuracy, system responses, latency distributions and evaluate quality metrics.</p>
        </div>

        {/* Evaluation execution triggers */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase' }}>Select Test Engine</span>
            <select 
              className="select-input"
              value={runMode}
              onChange={(e) => setRunMode(e.target.value)}
              style={{ padding: '6px 10px', fontSize: '0.8rem' }}
            >
              <option value="mock">Mock TF-IDF Engine</option>
              <option value="ollama" disabled={!ollamaStatus?.connected}>
                Ollama Engine {!ollamaStatus?.connected ? '(Offline)' : ''}
              </option>
            </select>
          </div>

          <button 
            className="btn-primary" 
            onClick={handleRunEvaluation}
            disabled={loading}
            style={{ padding: '8px 16px', fontSize: '0.85rem' }}
          >
            {loading ? (
              <RefreshCw size={14} className="status-dot loading" style={{ animation: 'spin 2s linear infinite' }} />
            ) : (
              <Play size={14} />
            )}
            Run Evaluation Suite
          </button>
        </div>
      </div>

      {/* Grid panels */}
      <div className="analytics-grid">
        
        {/* Stat 1: Total Chat Requests */}
        <div className="stat-card">
          <span className="stat-label">
            <Activity size={14} /> Total Requests
          </span>
          <span className="stat-value">{live.total_queries}</span>
          <span className="stat-desc">Chat sessions queries answered by API</span>
        </div>

        {/* Stat 2: Average User Latency */}
        <div className="stat-card teal">
          <span className="stat-label">
            <Clock size={14} style={{ color: 'var(--accent-teal)' }} /> Avg User Latency
          </span>
          <span className="stat-value">{live.average_latency_ms.toFixed(1)} ms</span>
          <span className="stat-desc">Round-trip search and answer compilation</span>
        </div>

        {/* Stat 3: Out-of-bounds Refusal Rate */}
        <div className="stat-card rose">
          <span className="stat-label">
            <ShieldAlert size={14} style={{ color: 'var(--accent-rose)' }} /> Refusal Rate
          </span>
          <span className="stat-value">{(live.refusal_rate * 100).toFixed(0)}%</span>
          <span className="stat-desc">{live.total_refusals} out of {live.total_queries} queries refused</span>
        </div>

        {/* Stat 4: Active Mode */}
        <div className="stat-card green">
          <span className="stat-label">
            <Cpu size={14} style={{ color: 'var(--accent-green)' }} /> Active Engine
          </span>
          <span className="stat-value" style={{ textTransform: 'capitalize' }}>{config.mode}</span>
          <span className="stat-desc">
            {config.mode === 'mock' ? 'Sparse cosine similarity matcher' : 'Dense vector matching & LLM'}
          </span>
        </div>

        {/* Benchmark Historical Trends Chart */}
        <div className="glass-panel chart-panel-large">
          <h3 className="panel-title" style={{ border: 'none', marginBottom: '0' }}>
            <BarChart2 size={16} style={{ color: 'var(--accent-violet)' }} /> Retrieval Quality Trend
          </h3>
          <div style={{ display: 'flex', gap: '16px', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-violet)', display: 'inline-block' }}></span>
              Precision @ 1
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-teal)', display: 'inline-block' }}></span>
              Recall @ 3
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ width: '8px', height: '8px', borderBottom: '2px dashed var(--accent-rose)', display: 'inline-block', width: '12px' }}></span>
              MRR
            </div>
          </div>
          <div className="chart-container">
            {renderHistoryChart()}
          </div>
        </div>

        {/* Latest Benchmark Score Panel */}
        <div className="glass-panel chart-panel-small" style={{ gap: '16px' }}>
          <h3 className="panel-title">
            <Award size={16} style={{ color: 'var(--accent-teal)' }} /> Benchmark Results
          </h3>
          
          {latest ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', flex: 1 }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Last run: {latest.timestamp} <br />
                Engine: <strong style={{ color: 'var(--text-primary)' }}>{latest.engine_mode.toUpperCase()}</strong>
              </div>

              <ProgressBar value={latest.metrics.precision_at_1} color="var(--accent-violet)" />
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', background: 'rgba(0,0,0,0.15)', padding: '12px', borderRadius: '10px', border: '1px solid var(--glass-border)', fontSize: '0.85rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Recall @ 3:</span>
                  <span style={{ color: '#fff', fontWeight: 600 }}>{(latest.metrics.recall_at_3 * 100).toFixed(0)}%</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>MRR score:</span>
                  <span style={{ color: '#fff', fontWeight: 600 }}>{latest.metrics.mrr.toFixed(2)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Refusal Acc:</span>
                  <span style={{ color: '#fff', fontWeight: 600 }}>{(latest.metrics.refusal_accuracy * 100).toFixed(0)}%</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Faithfulness:</span>
                  <span style={{ color: '#fff', fontWeight: 600 }}>{(latest.metrics.answer_faithfulness * 100).toFixed(0)}%</span>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Avg Latency Retrieval:</span>
                  <strong>{latest.metrics.avg_latency_retrieval_ms.toFixed(1)}ms</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Avg Latency Generation:</span>
                  <strong>{latest.metrics.avg_latency_generation_ms.toFixed(1)}ms</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Avg Latency Total:</span>
                  <strong>{latest.metrics.avg_latency_total_ms.toFixed(1)}ms</strong>
                </div>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center' }}>
              No benchmarks run yet. Use the top button to trigger evaluation metrics.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
