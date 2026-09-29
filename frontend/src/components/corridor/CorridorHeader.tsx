import React, { useState, useEffect } from 'react';
import { Train, RefreshCw, Moon, ArrowRight, Search, ShieldCheck } from 'lucide-react';
import { TrainState } from '../../types';

interface CorridorHeaderProps {
  selectedTrain: TrainState | null;
  trains: TrainState[];
  onSelectTrain: (trainId: string) => void;
  onSyncTrainNumber: (trainNumber: string) => Promise<boolean>;
  onReset: () => void;
  onOpenSwitchModal: () => void;
}

export const CorridorHeader: React.FC<CorridorHeaderProps> = ({
  selectedTrain,
  trains,
  onSelectTrain,
  onSyncTrainNumber,
  onReset,
  onOpenSwitchModal,
}) => {
  const [trainInput, setTrainInput] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [timeStr, setTimeStr] = useState<string>('23:47:33 IST');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const pad = (n: number) => n.toString().padStart(2, '0');
      setTimeStr(`${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())} IST`);
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleTrackSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanNum = trainInput.trim().replace(/^TRAIN_/i, '');
    if (!cleanNum) return;
    setIsSubmitting(true);
    try {
      const ok = await onSyncTrainNumber(cleanNum);
      if (ok) {
        setTrainInput('');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const trainDisplay = selectedTrain
    ? `${selectedTrain.train_number} — ${selectedTrain.train_name} (${selectedTrain.train_id})`
    : '12926 — Paschim Superfast Express (RS-2026-007)';

  return (
    <header
      style={{
        backgroundColor: '#070f1e',
        borderBottom: '1px solid #14284b',
        padding: '10px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px',
        flexWrap: 'wrap',
        zIndex: 100
      }}
    >
      {/* Brand & Subtitle */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
            padding: '8px',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 14px rgba(2, 132, 199, 0.45)'
          }}
        >
          <Train size={22} color="#ffffff" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.3px' }}>
              RailSutra
            </span>
          </div>
          <span style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 500 }}>
            Smarter Insights. Smoother Journeys.
          </span>
        </div>
      </div>

      {/* Corridor Title & Live Badges */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#e2e8f0' }}>
            Dynamic ETA Intelligence
          </div>
          <div style={{ fontSize: '0.7rem', color: '#64748b' }}>
            Analyze the entire railway corridor — not just the individual train.
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            style={{
              backgroundColor: 'rgba(56, 189, 248, 0.12)',
              color: '#38bdf8',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              padding: '2px 8px',
              borderRadius: '12px',
              fontSize: '0.65rem',
              fontWeight: 700
            }}
          >
            SIH 2026 PROTOTYPE
          </span>

          <span
            style={{
              backgroundColor: 'rgba(16, 185, 129, 0.12)',
              color: '#10b981',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              padding: '2px 8px',
              borderRadius: '12px',
              fontSize: '0.65rem',
              fontWeight: 700
            }}
          >
            DEMO MODE
          </span>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              backgroundColor: '#0c1a33',
              border: '1px solid #1e3a6c',
              padding: '3px 10px',
              borderRadius: '12px',
              fontSize: '0.68rem',
              color: '#94a3b8'
            }}
          >
            <Moon size={11} color="#38bdf8" />
            <span>Night Shift Operations, Team RailSutra</span>
          </div>

          <div
            style={{
              backgroundColor: '#0c1a33',
              border: '1px solid #1e3a6c',
              padding: '3px 10px',
              borderRadius: '12px',
              fontSize: '0.7rem',
              color: '#38bdf8',
              fontWeight: 700,
              fontFamily: 'monospace'
            }}
          >
            DEMO TIME • {timeStr}
          </div>
        </div>
      </div>

      {/* Train Number Input & Context Selector */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {/* Interactive Train Input Box */}
        <form onSubmit={handleTrackSubmit} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div
            style={{
              position: 'relative',
              display: 'flex',
              alignItems: 'center'
            }}
          >
            <input
              type="text"
              placeholder="Train # (e.g. 12926, 12951)..."
              value={trainInput}
              onChange={(e) => setTrainInput(e.target.value)}
              disabled={isSubmitting}
              style={{
                backgroundColor: '#0c1a33',
                border: '1px solid #2563eb',
                color: '#f8fafc',
                padding: '6px 10px 6px 28px',
                borderRadius: '6px',
                fontSize: '0.78rem',
                width: '180px',
                outline: 'none',
                boxShadow: '0 0 8px rgba(37, 99, 235, 0.25)'
              }}
            />
            <Search size={13} color="#38bdf8" style={{ position: 'absolute', left: '8px' }} />
          </div>

          <button
            type="submit"
            disabled={isSubmitting || !trainInput.trim()}
            style={{
              backgroundColor: '#0284c7',
              border: 'none',
              color: 'white',
              padding: '6px 12px',
              borderRadius: '6px',
              fontSize: '0.75rem',
              fontWeight: 700,
              cursor: isSubmitting ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              opacity: !trainInput.trim() ? 0.6 : 1
            }}
          >
            {isSubmitting ? (
              <RefreshCw size={12} className="spin" />
            ) : (
              <>
                <span>Track</span>
                <ArrowRight size={12} />
              </>
            )}
          </button>
        </form>

        {/* Selected Train Pill */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: '#0c1a33',
            border: '1px solid #1e3a6c',
            padding: '5px 12px',
            borderRadius: '20px',
            maxWidth: '320px',
            overflow: 'hidden'
          }}
        >
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: '#10b981',
              boxShadow: '0 0 6px #10b981',
              flexShrink: 0
            }}
          />
          <span
            style={{
              fontSize: '0.75rem',
              color: '#e2e8f0',
              fontWeight: 600,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis'
            }}
          >
            {trainDisplay}
          </span>
          <span
            style={{
              backgroundColor: '#0284c7',
              color: '#ffffff',
              fontSize: '0.65rem',
              fontWeight: 800,
              padding: '1px 5px',
              borderRadius: '4px',
              flexShrink: 0
            }}
          >
            RS
          </span>
        </div>

        {/* Switch Train Button */}
        <button
          onClick={onOpenSwitchModal}
          style={{
            backgroundColor: '#0284c7',
            color: '#ffffff',
            border: 'none',
            padding: '6px 14px',
            borderRadius: '6px',
            fontSize: '0.75rem',
            fontWeight: 800,
            cursor: 'pointer',
            letterSpacing: '0.5px'
          }}
        >
          SWITCH TRAIN
        </button>

        {/* Reset Button */}
        <button
          onClick={onReset}
          style={{
            backgroundColor: 'transparent',
            color: '#94a3b8',
            border: '1px solid #233554',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '0.75rem',
            fontWeight: 700,
            cursor: 'pointer'
          }}
        >
          RESET
        </button>
      </div>
    </header>
  );
};
