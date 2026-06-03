import React, { useState, useEffect } from 'react';
import { MessageSquare, BarChart2, Shield, Activity, RefreshCw } from 'lucide-react';
import ChatWindow from './components/ChatWindow';
import AnalyticsPanel from './components/AnalyticsPanel';
import SourceCard from './components/SourceCard';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' or 'analytics'
  const [config, setConfig] = useState({
    mode: 'mock', // 'mock' or 'ollama'
    embeddingModel: 'nomic-embed-text',
    llmModel: 'llama3',
  });
  const [ollamaStatus, setOllamaStatus] = useState({
    connected: false,
    url: 'http://localhost:11434',
    available_models: [],
  });
  const [apiOnline, setApiOnline] = useState(false);
  const [statusLoading, setStatusLoading] = useState(true);
  const [activeSource, setActiveSource] = useState(null); // FAQ item currently displayed in modal

  // Poll status endpoint to check if API and Ollama are reachable
  const checkStatus = () => {
    fetch('http://localhost:8000/api/status')
      .then((res) => res.json())
      .then((data) => {
        setApiOnline(true);
        setOllamaStatus(data.ollama);
        setStatusLoading(false);
      })
      .catch((err) => {
        console.error('API connection failure:', err);
        setApiOnline(false);
        setOllamaStatus({
          connected: false,
          url: 'http://localhost:11434',
          available_models: [],
        });
        setStatusLoading(false);
        // Force mock mode if API is down or Ollama is down and we are in ollama mode
        setConfig((prev) => ({ ...prev, mode: 'mock' }));
      });
  };

  useEffect(() => {
    checkStatus();
    // Check connection every 10 seconds
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-container">
      {/* Premium Glass Header */}
      <header className="glass-header">
        <div className="brand-section">
          <Shield size={24} style={{ color: 'var(--accent-violet)' }} />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1>ShopGlide Support</h1>
              <span className="brand-badge">RAG Assistant</span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
              Secure Customer Service Agent Demo
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="nav-tabs">
          <button
            className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            <MessageSquare size={16} />
            Support Chat
          </button>
          <button
            className={`tab-btn ${activeTab === 'analytics' ? 'active' : ''}`}
            onClick={() => setActiveTab('analytics')}
          >
            <BarChart2 size={16} />
            Analytics Dashboard
          </button>
        </nav>

        {/* Server & Ollama Status check */}
        <div className="connection-status">
          <span>Backend Status:</span>
          {statusLoading ? (
            <span className="status-dot loading" title="Checking systems..." />
          ) : (
            <span
              className={`status-dot ${apiOnline ? 'online' : ''}`}
              title={apiOnline ? 'API Server is Online' : 'API Server is Offline'}
            />
          )}
          
          <span style={{ marginLeft: '10px' }}>Ollama:</span>
          {statusLoading ? (
            <span className="status-dot loading" title="Checking systems..." />
          ) : (
            <span
              className={`status-dot ${ollamaStatus.connected ? 'online' : ''}`}
              title={ollamaStatus.connected ? `Ollama connected on ${ollamaStatus.url}` : 'Ollama Offline'}
            />
          )}
        </div>
      </header>

      {/* Main View Container */}
      <div className="view-container">
        {activeTab === 'chat' ? (
          <ChatWindow
            config={config}
            setConfig={setConfig}
            ollamaStatus={ollamaStatus}
            onOpenSource={setActiveSource}
          />
        ) : (
          <AnalyticsPanel
            config={config}
            ollamaStatus={ollamaStatus}
          />
        )}
      </div>

      {/* Modal for referenced source details */}
      {activeSource && (
        <SourceCard
          source={activeSource}
          onClose={() => setActiveSource(null)}
        />
      )}
    </div>
  );
}
