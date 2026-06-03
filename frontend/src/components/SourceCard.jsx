import React from 'react';
import { X, Tag, FileText, Bookmark } from 'lucide-react';

export default function SourceCard({ source, onClose }) {
  if (!source) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label="Close modal">
          <X size={20} />
        </button>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '12px' }}>
            <Bookmark size={20} style={{ color: 'var(--accent-teal)' }} />
            <div>
              <span className="brand-badge" style={{ fontSize: '0.65rem', padding: '2px 6px', background: 'rgba(6, 182, 212, 0.1)', borderColor: 'rgba(6, 182, 212, 0.3)', color: 'var(--accent-teal)' }}>
                {source.category}
              </span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '8px' }}>
                Ref ID: {source.id}
              </span>
            </div>
          </div>

          {/* Question */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <h3 style={{ color: 'var(--text-primary)', fontSize: '1.1rem', fontWeight: 600 }}>
              {source.question}
            </h3>
          </div>

          {/* Answer */}
          <div style={{ 
            background: 'rgba(0, 0, 0, 0.25)', 
            border: '1px solid var(--glass-border)', 
            borderRadius: '12px', 
            padding: '16px', 
            fontSize: '0.95rem', 
            lineHeight: 1.6, 
            color: 'rgba(255, 255, 255, 0.85)',
            maxHeight: '250px',
            overflowY: 'auto'
          }}>
            {source.answer}
          </div>

          {/* Tags */}
          {source.tags && source.tags.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginTop: '4px' }}>
              <Tag size={14} style={{ color: 'var(--text-muted)' }} />
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {source.tags.map((tag, idx) => (
                  <span 
                    key={idx} 
                    style={{ 
                      fontSize: '0.7rem', 
                      background: 'rgba(255, 255, 255, 0.03)', 
                      border: '1px solid var(--glass-border)', 
                      padding: '2px 8px', 
                      borderRadius: '4px',
                      color: 'var(--text-secondary)'
                    }}
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
