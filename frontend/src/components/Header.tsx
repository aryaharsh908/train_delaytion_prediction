import React from 'react';
import { Train, Activity, AlertTriangle, Cpu, Clock, ShieldAlert } from 'lucide-react';
import { SimulationState } from '../types';

interface HeaderProps {
  simulationState: SimulationState | null;
  onOpenModelMetrics: () => void;
  onOpenIncidentModal: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  simulationState,
  onOpenModelMetrics,
  onOpenIncidentModal
}) => {
  return (
    <header className="glass-panel" style={{ borderRadius: 0, borderTop: 0, borderLeft: 0, borderRight: 0, padding: '12px 24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        
        {/* Title & Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #0284c7 0%, #3b82f6 100%)',
            padding: '10px',
            borderRadius: '10px',
            boxShadow: '0 0 16px rgba(56, 189, 248, 0.4)'
          }}>
            <Train size={24} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.5px' }}>
                SIH26028 Dynamic ETA Forecast System
              </h1>
              <span style={{
                background: 'rgba(56, 189, 248, 0.15)',
                color: '#38bdf8',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                padding: '2px 8px',
                borderRadius: '6px',
                fontSize: '0.7rem',
                fontWeight: 700
              }}>
                MINISTRY OF RAILWAYS
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>
              Historical ML Base + Real-Time Telemetry + Kalman Filter + Graph Delay Propagation + Monte Carlo Uncertainty
            </p>
          </div>
        </div>

        {/* Center Disclaimers & Telemetry Feeds (Requirement #27) */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(245, 158, 11, 0.1)',
            border: '1px solid rgba(245, 158, 11, 0.25)',
            padding: '6px 12px',
            borderRadius: '8px',
            fontSize: '0.75rem',
            color: '#fbbf24'
          }}>
            <ShieldAlert size={14} />
            <span><strong>SIMULATION MODE</strong> | RTIS: MOCK | COA: MOCK</span>
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(15, 23, 42, 0.8)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            padding: '6px 12px',
            borderRadius: '8px',
            fontSize: '0.8rem',
            fontFamily: 'monospace',
            color: '#f8fafc'
          }}>
            <Clock size={14} color="#38bdf8" />
            <span>SIM TIME: {simulationState?.timestamp || '21:00:00'}</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button className="glass-button" onClick={onOpenModelMetrics}>
            <Cpu size={16} color="#a855f7" />
            <span>ML Model Evaluation</span>
          </button>
          
          <button className="glass-button glass-button-danger" onClick={onOpenIncidentModal}>
            <AlertTriangle size={16} />
            <span>Inject Incident</span>
          </button>
        </div>

      </div>
    </header>
  );
};
