import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, HelpCircle, ShieldAlert, Sparkles, BookOpen, Settings, RefreshCw, Cpu, Link2 } from 'lucide-react';

export default function ChatWindow({ config, setConfig, ollamaStatus, onOpenSource }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'bot',
      content: "Hello! I am **ShopGlide Support**, your internal RAG virtual assistant. I can answer your questions about our billing policies, shipping rates, security measures, external integrations, or partner agreements.\n\nAsk me anything, or click on a sample question from the list on the left to test!",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      sources: [],
      refused: false,
      engine: 'system'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [faqs, setFaqs] = useState([]);
  const [faqLoading, setFaqLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Fetch FAQ list for the explorer panel on load
  useEffect(() => {
    setFaqLoading(true);
    fetch('http://localhost:8000/api/faq')
      .then(res => res.json())
      .then(data => {
        setFaqs(data);
        setFaqLoading(false);
      })
      .catch(err => {
        console.error("Error fetching FAQs:", err);
        setFaqLoading(false);
      });
  }, []);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim()) return;

    if (!textToSend) setInput('');

    // User message
    const userMsg = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: query,
          mode: config.mode,
          embedding_model: config.embeddingModel,
          llm_model: config.llmModel
        })
      });

      if (!response.ok) {
        throw new Error(`Server returned error ${response.status}`);
      }

      const data = await response.json();
      
      const botMsg = {
        id: (Date.now() + 1).toString(),
        role: 'bot',
        content: data.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources: data.sources || [],
        refused: data.refused,
        engine: data.engine,
        confidence: data.confidence,
        latency: data.latency_ms
      };

      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      console.error("Chat error:", err);
      // Fallback error message
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'bot',
        content: "Oops! I encountered an error communicating with the backend server. Please verify the FastAPI backend is running and try again.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources: [],
        refused: true,
        engine: 'error'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-layout">
      {/* Sidebar Control Panel */}
      <div className="sidebar-panel">
        
        {/* Chat System Configuration */}
        <div className="glass-panel">
          <h3 className="panel-title">
            <Settings size={18} /> Configuration
          </h3>
          <div className="settings-group">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <span className="setting-label">Search Mode</span>
              <div className="toggle-container">
                <button 
                  className={`toggle-btn ${config.mode === 'mock' ? 'active' : ''}`}
                  onClick={() => setConfig(prev => ({ ...prev, mode: 'mock' }))}
                >
                  Mock (TF-IDF)
                </button>
                <button 
                  className={`toggle-btn ${config.mode === 'ollama' ? 'active' : ''}`}
                  disabled={!ollamaStatus?.connected}
                  onClick={() => setConfig(prev => ({ ...prev, mode: 'ollama' }))}
                  title={!ollamaStatus?.connected ? "Ollama server is offline" : "Switch to Ollama AI search"}
                >
                  Ollama AI
                </button>
              </div>
            </div>

            {config.mode === 'ollama' && (
              <>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '6px' }}>
                  <span className="setting-label">LLM Model</span>
                  <select 
                    className="select-input"
                    value={config.llmModel}
                    onChange={(e) => setConfig(prev => ({ ...prev, llmModel: e.target.value }))}
                  >
                    {ollamaStatus?.available_models?.length > 0 ? (
                      ollamaStatus.available_models.map(m => (
                        <option key={m} value={m}>{m}</option>
                      ))
                    ) : (
                      <option value="llama3">llama3 (Default)</option>
                    )}
                  </select>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span className="setting-label">Embedding Model</span>
                  <select 
                    className="select-input"
                    value={config.embeddingModel}
                    onChange={(e) => setConfig(prev => ({ ...prev, embeddingModel: e.target.value }))}
                  >
                    {ollamaStatus?.available_models?.length > 0 ? (
                      ollamaStatus.available_models.map(m => (
                        <option key={m} value={m}>{m}</option>
                      ))
                    ) : (
                      <option value="nomic-embed-text">nomic-embed-text (Default)</option>
                    )}
                  </select>
                </div>
              </>
            )}

            <div style={{ 
              fontSize: '0.75rem', 
              color: 'var(--text-secondary)', 
              background: 'rgba(255,255,255,0.02)', 
              padding: '10px', 
              borderRadius: '8px', 
              border: '1px solid var(--glass-border)',
              marginTop: '6px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Cpu size={12} style={{ color: 'var(--accent-teal)' }} />
                <strong>RAG Engine Status</strong>
              </div>
              <div>Active Index: <strong>{faqs.length} FAQ Items</strong></div>
              <div>Ollama Server: <strong>{ollamaStatus?.connected ? 'Connected' : 'Offline'}</strong></div>
            </div>
          </div>
        </div>

        {/* Knowledge Explorer & Prompt Injector */}
        <div className="glass-panel" style={{ flex: 1, minHeight: 0 }}>
          <h3 className="panel-title">
            <BookOpen size={18} /> Internal FAQ Docs
          </h3>
          {faqLoading ? (
            <div style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center' }}>
              <RefreshCw size={24} className="status-dot loading" style={{ animation: 'spin 2s linear infinite' }} />
            </div>
          ) : (
            <div className="faq-category-list">
              {faqs.map(faq => (
                <button 
                  key={faq.id} 
                  className="faq-list-item"
                  onClick={() => handleSend(faq.question)}
                  title="Click to run this FAQ question through RAG"
                >
                  <span className="category-tag">{faq.category}</span>
                  <div style={{ fontWeight: 500, color: 'var(--text-primary)', textOverflow: 'ellipsis', whiteSpace: 'nowrap', overflow: 'hidden' }}>
                    {faq.question}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Chat Pane */}
      <div className="chat-pane glass-panel">
        {/* Chat Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--glass-border)', paddingBottom: '12px', marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Sparkles size={20} style={{ color: 'var(--accent-violet)' }} />
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Active Support Assistant</h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Powered by {config.mode === 'mock' ? 'Mock Sparse TF-IDF Matcher' : `Ollama (${config.llmModel})`}
              </p>
            </div>
          </div>
        </div>

        {/* Chat Message Panel */}
        <div className="chat-history">
          {messages.map((msg) => (
            <div key={msg.id} className={`message-bubble ${msg.role}`}>
              <div className="avatar">
                {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <div className="message-content">
                  {msg.content}

                  {/* Bot reference tags */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="sources-container">
                      <div className="sources-header">
                        <Link2 size={12} /> Sources Found
                      </div>
                      <div className="sources-list">
                        {msg.sources.map((src, idx) => (
                          <div 
                            key={idx} 
                            className="source-tag"
                            onClick={() => onOpenSource(src)}
                            title="Click to view full FAQ source text"
                          >
                            <span>[{idx + 1}] {src.question.slice(0, 25)}...</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="message-meta">
                  <span>{msg.timestamp}</span>
                  {msg.role === 'bot' && (
                    <>
                      <span>•</span>
                      <span>Engine: {msg.engine}</span>
                      {msg.confidence !== undefined && msg.confidence > 0 && (
                        <>
                          <span>•</span>
                          <span>Score: {msg.confidence.toFixed(2)}</span>
                        </>
                      )}
                      {msg.latency && (
                        <>
                          <span>•</span>
                          <span>Time: {msg.latency.total.toFixed(0)}ms</span>
                        </>
                      )}
                      {msg.refused && (
                        <span className="refusal-badge">Refusal</span>
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message-bubble bot">
              <div className="avatar">
                <Bot size={18} />
              </div>
              <div className="message-content" style={{ display: 'flex', alignItems: 'center', height: '44px' }}>
                <div className="typing-indicator">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input Bar */}
        <div className="chat-input-bar">
          <input 
            type="text" 
            className="chat-text-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Ask about billing, refunds, tracking shipping, password security..."
            disabled={isLoading}
          />
          <button 
            className="send-btn"
            onClick={() => handleSend()}
            disabled={isLoading || !input.trim()}
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
