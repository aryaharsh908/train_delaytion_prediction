import React, { useState } from 'react';
import { X, Search, Train, ArrowRight, RefreshCw, CheckCircle } from 'lucide-react';
import { TrainState } from '../../types';

interface SwitchTrainModalProps {
  isOpen: boolean;
  onClose: () => void;
  trains: TrainState[];
  selectedTrainId: string;
  onSelectTrain: (trainId: string) => void;
  onSyncTrainNumber: (trainNumber: string) => Promise<boolean>;
}

export const SwitchTrainModal: React.FC<SwitchTrainModalProps> = ({
  isOpen,
  onClose,
  trains,
  selectedTrainId,
  onSelectTrain,
  onSyncTrainNumber
}) => {
  const [inputNum, setInputNum] = useState<string>('');
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanNum = inputNum.trim().replace(/^TRAIN_/i, '');
    if (!cleanNum) {
      setErrorMsg('Please enter a valid train number.');
      return;
    }
    setErrorMsg(null);
    setIsSyncing(true);
    try {
      const ok = await onSyncTrainNumber(cleanNum);
      if (ok) {
        onClose();
      } else {
        setErrorMsg(`Train ${cleanNum} could not be loaded. Please verify the train number.`);
      }
    } catch (err: any) {
      setErrorMsg(err?.message || `Failed to sync train ${cleanNum}`);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleQuickSelect = (trainNum: string) => {
    onSelectTrain(trainNum);
    onClose();
  };

  const quickPicks = [
    { number: '12926', name: 'Paschim Superfast Express' },
    { number: '12951', name: 'Mumbai Rajdhani Express' },
    { number: '12952', name: 'New Delhi Tejas Rajdhani' },
    { number: '12954', name: 'August Kranti Tejas Rajdhani' },
    { number: '12626', name: 'Kerala Express' },
    { number: '12302', name: 'Kolkata Rajdhani Express' }
  ];

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(3, 7, 18, 0.75)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 5000,
        padding: '20px'
      }}
    >
      <div
        style={{
          backgroundColor: '#0c1a33',
          border: '1px solid #1e3a6c',
          borderRadius: '12px',
          width: '100%',
          maxWidth: '520px',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6)'
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                backgroundColor: '#0284c7',
                padding: '8px',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Train size={18} color="#ffffff" />
            </div>
            <div>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#f8fafc' }}>
                Switch Global Intelligence Context
              </div>
              <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
                Enter any Indian Railways train number to track live telemetry & forecasts.
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              backgroundColor: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '4px'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <label style={{ fontSize: '0.72rem', fontWeight: 700, color: '#94a3b8' }}>
            ENTER TRAIN NUMBER
          </label>
          <div style={{ display: 'flex', gap: '8px' }}>
            <div style={{ position: 'relative', flex: 1, display: 'flex', alignItems: 'center' }}>
              <input
                type="text"
                placeholder="e.g. 12926, 12951, 12626..."
                value={inputNum}
                onChange={(e) => {
                  setInputNum(e.target.value);
                  setErrorMsg(null);
                }}
                autoFocus
                style={{
                  width: '100%',
                  backgroundColor: '#081224',
                  border: '1px solid #2563eb',
                  color: '#f8fafc',
                  padding: '10px 14px 10px 36px',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  fontWeight: 700,
                  outline: 'none',
                  boxShadow: '0 0 10px rgba(37, 99, 235, 0.25)'
                }}
              />
              <Search size={16} color="#38bdf8" style={{ position: 'absolute', left: '12px' }} />
            </div>

            <button
              type="submit"
              disabled={isSyncing || !inputNum.trim()}
              style={{
                backgroundColor: '#0284c7',
                border: 'none',
                color: 'white',
                padding: '10px 18px',
                borderRadius: '8px',
                fontSize: '0.85rem',
                fontWeight: 800,
                cursor: isSyncing ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                opacity: !inputNum.trim() ? 0.6 : 1
              }}
            >
              {isSyncing ? (
                <RefreshCw size={14} className="spin" />
              ) : (
                <>
                  <span>Track</span>
                  <ArrowRight size={14} />
                </>
              )}
            </button>
          </div>

          {errorMsg && (
            <div style={{ fontSize: '0.75rem', color: '#f87171', marginTop: '4px' }}>
              {errorMsg}
            </div>
          )}
        </form>

        {/* Quick Corridor Selection */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#64748b', letterSpacing: '0.5px' }}>
            OR SELECT FROM ACTIVE CORRIDOR TRAINS
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '220px', overflowY: 'auto' }}>
            {quickPicks.map((qp) => {
              const isSelected = selectedTrainId.includes(qp.number);
              return (
                <div
                  key={qp.number}
                  onClick={() => handleQuickSelect(qp.number)}
                  style={{
                    backgroundColor: isSelected ? 'rgba(2, 132, 199, 0.2)' : '#081224',
                    border: `1px solid ${isSelected ? '#0284c7' : '#14284b'}`,
                    padding: '10px 14px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    transition: 'all 0.15s'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 800, color: '#38bdf8' }}>
                      {qp.number}
                    </span>
                    <span style={{ fontSize: '0.82rem', color: '#f8fafc', fontWeight: 600 }}>
                      {qp.name}
                    </span>
                  </div>

                  {isSelected && (
                    <span style={{ fontSize: '0.68rem', color: '#10b981', fontWeight: 800 }}>
                      ACTIVE
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
