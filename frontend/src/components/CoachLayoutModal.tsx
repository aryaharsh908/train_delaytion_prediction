import React from 'react';
import { X, Train, Shield, Check } from 'lucide-react';
import { TrainState } from '../types';

interface CoachLayoutModalProps {
  train: TrainState | null;
  onClose: () => void;
}

export const CoachLayoutModal: React.FC<CoachLayoutModalProps> = ({ train, onClose }) => {
  if (!train) return null;

  // Realistic coach compositions based on train type
  const isRajdhani = train.train_type === 'RAJDHANI';
  const isShatabdi = train.train_type === 'SHATABDI';

  const coaches = isRajdhani ? [
    { code: 'ENG', name: 'WAP-7 Engine', type: 'LOCO', color: '#38bdf8' },
    { code: 'EOG', name: 'Generator Car', type: 'POWER', color: '#64748b' },
    { code: 'H1', name: 'First AC (1A)', type: 'AC_FIRST', color: '#fbbf24' },
    { code: 'A1', name: '2-Tier AC (2A)', type: 'AC_2TIER', color: '#a855f7' },
    { code: 'A2', name: '2-Tier AC (2A)', type: 'AC_2TIER', color: '#a855f7' },
    { code: 'B1', name: '3-Tier AC (3A)', type: 'AC_3TIER', color: '#3b82f6' },
    { code: 'B2', name: '3-Tier AC (3A)', type: 'AC_3TIER', color: '#3b82f6' },
    { code: 'B3', name: '3-Tier AC (3A)', type: 'AC_3TIER', color: '#3b82f6' },
    { code: 'PC', name: 'Pantry Car', type: 'PANTRY', color: '#ef4444' },
    { code: 'B4', name: '3-Tier AC (3A)', type: 'AC_3TIER', color: '#3b82f6' },
    { code: 'B5', name: '3-Tier AC (3A)', type: 'AC_3TIER', color: '#3b82f6' },
    { code: 'M1', name: '3 AC Economy (3E)', type: 'AC_3ECONOMY', color: '#06b6d4' },
    { code: 'EOG', name: 'Guard & Power Car', type: 'POWER', color: '#64748b' }
  ] : isShatabdi ? [
    { code: 'ENG', name: 'WAP-7 Engine', type: 'LOCO', color: '#38bdf8' },
    { code: 'EOG', name: 'Power Car', type: 'POWER', color: '#64748b' },
    { code: 'E1', name: 'Executive Anubhuti', type: 'EXEC', color: '#f59e0b' },
    { code: 'E2', name: 'Executive Chair Car', type: 'EXEC', color: '#f59e0b' },
    { code: 'C1', name: 'AC Chair Car', type: 'CHAIR', color: '#3b82f6' },
    { code: 'C2', name: 'AC Chair Car', type: 'CHAIR', color: '#3b82f6' },
    { code: 'C3', name: 'AC Chair Car', type: 'CHAIR', color: '#3b82f6' },
    { code: 'C4', name: 'AC Chair Car', type: 'CHAIR', color: '#3b82f6' },
    { code: 'C5', name: 'AC Chair Car', type: 'CHAIR', color: '#3b82f6' },
    { code: 'EOG', name: 'Guard Car', type: 'POWER', color: '#64748b' }
  ] : [
    { code: 'ENG', name: 'WAP-4 Engine', type: 'LOCO', color: '#38bdf8' },
    { code: 'SLR', name: 'Luggage / Guard', type: 'SLR', color: '#64748b' },
    { code: 'GS', name: 'General Unreserved', type: 'GEN', color: '#94a3b8' },
    { code: 'S1', name: 'Sleeper Class', type: 'SLEEPER', color: '#10b981' },
    { code: 'S2', name: 'Sleeper Class', type: 'SLEEPER', color: '#10b981' },
    { code: 'S3', name: 'Sleeper Class', type: 'SLEEPER', color: '#10b981' },
    { code: 'B1', name: '3-Tier AC', type: 'AC_3TIER', color: '#3b82f6' },
    { code: 'B2', name: '3-Tier AC', type: 'AC_3TIER', color: '#3b82f6' },
    { code: 'A1', name: '2-Tier AC', type: 'AC_2TIER', color: '#a855f7' },
    { code: 'PC', name: 'Pantry Car', type: 'PANTRY', color: '#ef4444' },
    { code: 'S4', name: 'Sleeper Class', type: 'SLEEPER', color: '#10b981' },
    { code: 'SLR', name: 'Guard Car', type: 'SLR', color: '#64748b' }
  ];

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(2, 6, 23, 0.85)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 2000,
      padding: '20px'
    }}>
      <div className="glass-panel" style={{
        width: '100%',
        maxWidth: '750px',
        maxHeight: '90vh',
        overflowY: 'auto',
        borderRadius: '16px',
        border: '1px solid rgba(255, 255, 255, 0.15)',
        boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6)',
        padding: '24px'
      }}>
        
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', paddingBottom: '14px', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Train size={22} color="#38bdf8" />
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#f8fafc' }}>
                Typical {train.train_type} Rake Composition
              </h3>
              <p style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                {train.train_number} - {train.train_name} ({train.origin_station_name} ➔ {train.destination_station_name})
              </p>
            </div>
          </div>

          <button onClick={onClose} className="glass-button" style={{ padding: '6px', borderRadius: '50%' }}>
            <X size={18} />
          </button>
        </div>

        {/* Train Rake Horizontal Scrollable Display */}
        <div style={{
          display: 'flex',
          gap: '8px',
          overflowX: 'auto',
          padding: '16px 8px',
          background: 'rgba(15, 23, 42, 0.6)',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.05)',
          marginBottom: '20px'
        }}>
          {coaches.map((c, idx) => (
            <div key={idx} style={{
              minWidth: '68px',
              height: '75px',
              background: 'rgba(30, 41, 59, 0.8)',
              border: `2px solid ${c.color}`,
              borderRadius: '8px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '4px',
              position: 'relative',
              boxShadow: `0 0 10px ${c.color}22`
            }}>
              <span style={{ fontSize: '0.65rem', color: '#94a3b8', fontWeight: 600 }}>
                {idx === 0 ? 'FRONT' : `#${idx}`}
              </span>
              <span style={{ fontSize: '1.05rem', fontWeight: 900, color: c.color, margin: '2px 0' }}>
                {c.code}
              </span>
              <span style={{ fontSize: '0.62rem', color: '#cbd5e1', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden', maxWidth: '60px' }}>
                {c.type}
              </span>
            </div>
          ))}
        </div>

        {/* Legend Table */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '0.8rem', color: '#94a3b8' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(30, 41, 59, 0.3)', padding: '8px 12px', borderRadius: '8px' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#fbbf24' }} />
            <span>First AC (1A) / Executive</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(30, 41, 59, 0.3)', padding: '8px 12px', borderRadius: '8px' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#a855f7' }} />
            <span>2-Tier AC (2A)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(30, 41, 59, 0.3)', padding: '8px 12px', borderRadius: '8px' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#3b82f6' }} />
            <span>3-Tier AC (3A) / Chair Car</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(30, 41, 59, 0.3)', padding: '8px 12px', borderRadius: '8px' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444' }} />
            <span>Hot Buffet Pantry Car</span>
          </div>
        </div>

        <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end' }}>
          <button className="glass-button glass-button-primary" onClick={onClose}>
            <Check size={16} />
            <span>Got It</span>
          </button>
        </div>

      </div>
    </div>
  );
};
