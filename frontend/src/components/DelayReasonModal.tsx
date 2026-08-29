import React from 'react';
import { X, Info, AlertTriangle } from 'lucide-react';
import { StationRouteItem } from '../types';

interface DelayReasonModalProps {
  station: StationRouteItem | null;
  onClose: () => void;
}

export const DelayReasonModal: React.FC<DelayReasonModalProps> = ({ station, onClose }) => {
  if (!station) return null;

  const isDelayed = station.arrival_delay_minutes > 0;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      animation: 'fadeIn 0.2s ease-out'
    }}>
      <div className="glass-panel" style={{ width: '420px', padding: '24px', position: 'relative', borderRadius: '16px' }}>
        
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              background: isDelayed ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
              padding: '8px',
              borderRadius: '10px'
            }}>
              {isDelayed ? <AlertTriangle color="#ef4444" size={20} /> : <Info color="#34d399" size={20} />}
            </div>
            <div>
              <h3 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.1rem', fontWeight: 700 }}>
                {station.station_name} ({station.station_code})
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                {station.platform_number} • {station.distance_km} km
              </span>
            </div>
          </div>

          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {/* Delay summary badge */}
        <div style={{
          background: isDelayed ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
          border: isDelayed ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: '10px',
          padding: '12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '16px'
        }}>
          <div>
            <span style={{ fontSize: '0.7rem', color: '#94a3b8', display: 'block' }}>SCHEDULED VS FORECAST</span>
            <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc', marginTop: '2px' }}>
              Scheduled: {station.scheduled_arrival} → <span style={{ color: isDelayed ? '#ef4444' : '#34d399' }}>Expected: {station.forecasted_arrival}</span>
            </div>
          </div>

          <div style={{
            background: isDelayed ? '#ef4444' : '#10b981',
            color: 'white',
            fontWeight: 800,
            padding: '4px 10px',
            borderRadius: '20px',
            fontSize: '0.8rem'
          }}>
            {isDelayed ? `+${station.arrival_delay_minutes} min late` : 'On Time'}
          </div>
        </div>

        {/* Cascading 8-Factor Delay Breakdown & Section Recovery */}
        {station.cascading_breakdown && isDelayed && (
          <div style={{
            background: 'rgba(15, 23, 42, 0.9)',
            border: '1px solid rgba(56, 189, 248, 0.25)',
            borderRadius: '10px',
            padding: '12px',
            marginBottom: '16px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8' }}>
                CASCADING DELAY PROPAGATION (8 FACTORS)
              </span>
              {station.section_recovery_minutes !== undefined && station.section_recovery_minutes < 0 && (
                <span style={{
                  background: 'rgba(16, 185, 129, 0.2)',
                  color: '#34d399',
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                  padding: '2px 8px',
                  borderRadius: '10px',
                  fontSize: '0.7rem',
                  fontWeight: 700
                }}>
                  ⚡ {station.section_recovery_minutes} min recovered!
                </span>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '0.75rem' }}>
              <div style={{ color: '#cbd5e1' }}>• Initial Delay: <strong style={{ color: '#f87171' }}>+{station.cascading_breakdown.initial_delay}m</strong></div>
              <div style={{ color: '#cbd5e1' }}>• Wait for Train: <strong style={{ color: '#f87171' }}>+{station.cascading_breakdown.train_wait}m</strong></div>
              <div style={{ color: '#cbd5e1' }}>• Signal Restriction: <strong style={{ color: '#f87171' }}>+{station.cascading_breakdown.signal_restriction}m</strong></div>
              <div style={{ color: '#cbd5e1' }}>• Platform Hold: <strong style={{ color: '#f87171' }}>+{station.cascading_breakdown.platform_occupied}m</strong></div>
              <div style={{ color: '#cbd5e1' }}>• Slow Section: <strong style={{ color: '#f87171' }}>+{station.cascading_breakdown.slow_section}m</strong></div>
              <div style={{ color: '#cbd5e1' }}>• Freight Ahead: <strong style={{ color: '#f87171' }}>+{station.cascading_breakdown.freight_ahead}m</strong></div>
              <div style={{ color: '#cbd5e1' }}>• Crew Issue: <strong style={{ color: '#f87171' }}>+{station.cascading_breakdown.crew_issue}m</strong></div>
              <div style={{ color: '#cbd5e1' }}>• Junction Congestion: <strong style={{ color: '#f87171' }}>+{station.cascading_breakdown.junction_congestion}m</strong></div>
            </div>
          </div>
        )}

        {/* Reasons List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', letterSpacing: '0.5px' }}>
            EXPLAINABLE DELAY REASONS (DYNAMIC ENGINE):
          </span>

          {station.delay_reasons.length === 0 ? (
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', background: 'rgba(15,23,42,0.6)', padding: '12px', borderRadius: '8px' }}>
              No operational delays reported for this station. Train running on schedule.
            </div>
          ) : (
            station.delay_reasons.map((r, idx) => (
              <div key={idx} style={{
                background: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '8px',
                padding: '10px 12px',
                display: 'flex',
                alignItems: 'flex-start',
                justifyContent: 'space-between',
                gap: '10px'
              }}>
                <div>
                  <strong style={{ fontSize: '0.82rem', color: '#f8fafc', display: 'block' }}>{r.factor_name}</strong>
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{r.description}</span>
                </div>
                <span style={{
                  fontFamily: 'monospace',
                  fontWeight: 700,
                  fontSize: '0.85rem',
                  color: r.impact_minutes > 0 ? '#ef4444' : '#34d399'
                }}>
                  {r.impact_minutes > 0 ? `+${r.impact_minutes}m` : `${r.impact_minutes}m`}
                </span>
              </div>
            ))
          )}
        </div>


      </div>
    </div>
  );
};
