import React from 'react';
import { Play, Pause, RotateCcw, FastForward, Activity } from 'lucide-react';
import { SimulationState } from '../types';

interface ControlPanelProps {
  simulationState: SimulationState | null;
  onStart: () => void;
  onPause: () => void;
  onReset: () => void;
  onSetSpeed: (multiplier: number) => void;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  simulationState,
  onStart,
  onPause,
  onReset,
  onSetSpeed
}) => {
  const isRunning = simulationState?.is_running ?? true;
  const speed = simulationState?.speed_multiplier ?? 5;

  return (
    <div className="glass-panel" style={{ padding: '10px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px' }}>
      
      {/* Play / Pause / Reset */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {isRunning ? (
          <button className="glass-button" onClick={onPause} title="Pause Simulation">
            <Pause size={16} color="#f59e0b" />
            <span>Pause</span>
          </button>
        ) : (
          <button className="glass-button glass-button-primary" onClick={onStart} title="Start Simulation">
            <Play size={16} />
            <span>Play</span>
          </button>
        )}

        <button className="glass-button" onClick={onReset} title="Reset Simulation State">
          <RotateCcw size={16} color="#94a3b8" />
          <span>Reset</span>
        </button>
      </div>

      {/* Speed Selector */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <span style={{ fontSize: '0.75rem', color: '#94a3b8', marginRight: '4px' }}>SIM SPEED:</span>
        {[1, 5, 20].map((s) => (
          <button
            key={s}
            onClick={() => onSetSpeed(s)}
            className="glass-button"
            style={{
              padding: '4px 10px',
              fontSize: '0.75rem',
              background: speed === s ? 'rgba(56, 189, 248, 0.25)' : 'rgba(30, 41, 59, 0.6)',
              borderColor: speed === s ? '#38bdf8' : 'rgba(255,255,255,0.1)',
              color: speed === s ? '#38bdf8' : '#94a3b8'
            }}
          >
            {s}x
          </button>
        ))}
      </div>

      {/* Active Monitors */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '0.75rem', color: '#94a3b8' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Activity size={14} color="#10b981" />
          <span>ACTIVE TRAINS: <strong>{simulationState?.trains.length ?? 0}</strong></span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span className="pulse-dot pulse-dot-amber"></span>
          <span>INCIDENTS: <strong>{simulationState?.active_events_count ?? 0}</strong></span>
        </div>
      </div>

    </div>
  );
};
