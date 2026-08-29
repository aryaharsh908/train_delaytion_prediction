import React from 'react';
import { X, Train, Clock, HelpCircle, ArrowRight, ShieldCheck, Zap, AlertCircle } from 'lucide-react';
import { TrainState } from '../types';
import { MonteCarloChart } from './MonteCarloChart';

interface TrainDrawerProps {
  train: TrainState | null;
  onClose: () => void;
}

export const TrainDrawer: React.FC<TrainDrawerProps> = ({ train, onClose }) => {
  if (!train) return null;

  const eta = train.current_eta;
  const statusBadgeClass =
    train.status === 'ON_TIME'
      ? 'badge-on-time'
      : train.status === 'SLIGHT_DELAY'
      ? 'badge-slight-delay'
      : train.status === 'CRITICAL_DELAY'
      ? 'badge-critical-delay'
      : 'badge-incident';

  return (
    <div className="glass-panel" style={{
      position: 'fixed',
      top: '70px',
      right: '16px',
      bottom: '16px',
      width: '440px',
      zIndex: 900,
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      boxShadow: '-8px 0 32px rgba(0,0,0,0.5)',
      animation: 'fadeIn 0.25s ease-out'
    }}>
      
      {/* Drawer Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ background: 'rgba(56, 189, 248, 0.15)', padding: '8px', borderRadius: '8px' }}>
            <Train size={20} color="#38bdf8" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.1rem', fontWeight: 700 }}>
                {train.train_number} - {train.train_name}
              </h3>
            </div>
            <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
              {train.origin_station_name} <ArrowRight size={10} /> {train.destination_station_name} ({train.train_type})
            </p>
          </div>
        </div>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
          <X size={20} />
        </button>
      </div>

      {/* Content Container */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        
        {/* Telemetry Strip */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
          <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '8px 10px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
            <div style={{ fontSize: '0.68rem', color: '#64748b' }}>SPEED</div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: '#38bdf8' }}>{train.speed_kmh} <span style={{ fontSize: '0.7rem' }}>km/h</span></div>
          </div>
          <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '8px 10px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
            <div style={{ fontSize: '0.68rem', color: '#64748b' }}>CURRENT DELAY</div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: train.current_delay_minutes > 15 ? '#ef4444' : '#fbbf24' }}>
              +{Math.round(train.current_delay_minutes)} <span style={{ fontSize: '0.7rem' }}>min</span>
            </div>
          </div>
          <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '8px 10px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
            <div style={{ fontSize: '0.68rem', color: '#64748b' }}>STATUS</div>
            <div style={{ marginTop: '2px' }}>
              <span className={`badge ${statusBadgeClass}`}>{train.status}</span>
            </div>
          </div>
        </div>

        {/* Dynamic ETA Forecast Box */}
        {eta && (
          <div className="glass-panel-glow" style={{ padding: '16px', borderRadius: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', letterSpacing: '0.5px' }}>
                DYNAMIC FORECASTED ETA
              </span>
              <span style={{ fontSize: '0.68rem', color: '#64748b' }}>Updated {eta.last_updated}</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px', marginBottom: '12px' }}>
              <div style={{ fontSize: '2rem', fontWeight: 800, fontFamily: 'Outfit, sans-serif', color: '#f8fafc' }}>
                {eta.dynamic_forecast_eta}
              </div>
              <div style={{ fontSize: '0.85rem', color: '#fbbf24', fontWeight: 600 }}>
                (+{Math.round(eta.total_predicted_delay_minutes)} min total delay)
              </div>
            </div>

            {/* Comparison row */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.75rem', borderTop: '1px dashed rgba(255,255,255,0.1)', paddingTop: '8px' }}>
              <div>
                <span style={{ color: '#64748b' }}>Timetable Schedule: </span>
                <span style={{ color: '#94a3b8', textDecoration: 'line-through' }}>{eta.timetable_baseline_eta}</span>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>ML Baseline Model: </span>
                <span style={{ color: '#a855f7' }}>{eta.ml_base_eta}</span>
              </div>
            </div>
          </div>
        )}

        {/* Explainability Breakdown (Waterfall) */}
        {eta && eta.explainability_factors && (
          <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '14px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <Zap size={16} color="#f59e0b" />
              <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f8fafc' }}>
                ETA Change Explanation Breakdown
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {eta.explainability_factors.map((factor, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ color: '#e2e8f0', fontWeight: 500 }}>{factor.factor_name}</span>
                    <span style={{ fontSize: '0.7rem', color: '#64748b' }}>{factor.description}</span>
                  </div>
                  <span style={{
                    fontWeight: 700,
                    color: factor.impact_minutes > 0 ? '#ef4444' : factor.impact_minutes < 0 ? '#34d399' : '#94a3b8',
                    fontFamily: 'monospace'
                  }}>
                    {factor.impact_minutes > 0 ? `+${factor.impact_minutes}m` : `${factor.impact_minutes}m`}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Monte Carlo Uncertainty & Confidence Intervals */}
        {eta && (
          <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '14px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldCheck size={16} color="#34d399" />
                <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f8fafc' }}>
                  Monte Carlo Uncertainty & Confidence
                </span>
              </div>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#34d399' }}>
                {Math.round(eta.on_time_probability * 100)}% On-Time
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.75rem', marginBottom: '8px' }}>
              <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '6px 8px', borderRadius: '6px' }}>
                <span style={{ color: '#64748b', display: 'block', fontSize: '0.68rem' }}>80% CONFIDENCE RANGE</span>
                <strong style={{ color: '#38bdf8' }}>{eta.confidence_80_min} — {eta.confidence_80_max}</strong>
              </div>
              <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '6px 8px', borderRadius: '6px' }}>
                <span style={{ color: '#64748b', display: 'block', fontSize: '0.68rem' }}>95% CONFIDENCE RANGE</span>
                <strong style={{ color: '#a855f7' }}>{eta.confidence_95_min} — {eta.confidence_95_max}</strong>
              </div>
            </div>

            {/* Monte Carlo Density Chart */}
            <MonteCarloChart samples={eta.monte_carlo_samples && eta.monte_carlo_samples.length > 0 ? eta.monte_carlo_samples : [10, 12, 14, 15, 18, 19, 21, 22, 23, 24, 25, 26, 27, 28, 30, 32, 35]} />
          </div>
        )}

      </div>
    </div>
  );
};
