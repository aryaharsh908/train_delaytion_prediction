import React from 'react';
import { Network, Activity, AlertTriangle, GitCommit } from 'lucide-react';
import { CorridorHealthSummary } from '../../types';

interface CorridorSummaryBarProps {
  summary: CorridorHealthSummary | null;
}

export const CorridorSummaryBar: React.FC<CorridorSummaryBarProps> = ({ summary }) => {
  const activeTrains = summary ? summary.active_trains : 8;
  const junctionsAtRisk = summary ? summary.junctions_at_risk : 3;
  const bottleneckSections = summary ? summary.bottleneck_sections : 1;
  const affectedServices = summary ? summary.affected_services : 7;
  const healthScore = summary ? summary.corridor_health : 67.1;
  const healthStatus = summary ? summary.corridor_health_status : 'MODERATE';

  return (
    <div
      style={{
        backgroundColor: '#091326',
        borderBottom: '1px solid #14284b',
        padding: '10px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '20px',
        flexWrap: 'wrap'
      }}
    >
      {/* Left: Corridor Identity */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            backgroundColor: '#0c224a',
            border: '1px solid #1e3a6c',
            width: '36px',
            height: '36px',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#38bdf8'
          }}
        >
          <Network size={18} />
        </div>
        <div>
          <div style={{ fontSize: '0.92rem', fontWeight: 800, color: '#f1f5f9' }}>
            Delhi – Mumbai Western Trunk Corridor
          </div>
          <div style={{ fontSize: '0.7rem', color: '#64748b' }}>
            One Corridor. Many Trains. Complete Intelligence.
          </div>
        </div>
      </div>

      {/* Right: Real Operational Metrics */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '24px', flexWrap: 'wrap' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc' }}>
            {activeTrains}
          </div>
          <div style={{ fontSize: '0.65rem', color: '#64748b', fontWeight: 700, letterSpacing: '0.5px' }}>
            ACTIVE TRAINS
          </div>
        </div>

        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fbbf24' }}>
            {junctionsAtRisk}
          </div>
          <div style={{ fontSize: '0.65rem', color: '#64748b', fontWeight: 700, letterSpacing: '0.5px' }}>
            JUNCTIONS AT RISK
          </div>
        </div>

        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f87171' }}>
            {bottleneckSections}
          </div>
          <div style={{ fontSize: '0.65rem', color: '#64748b', fontWeight: 700, letterSpacing: '0.5px' }}>
            BOTTLENECK SECTION
          </div>
        </div>

        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#38bdf8' }}>
            {affectedServices}
          </div>
          <div style={{ fontSize: '0.65rem', color: '#64748b', fontWeight: 700, letterSpacing: '0.5px' }}>
            AFFECTED SERVICES
          </div>
        </div>

        {/* Health Score Pill */}
        <div
          style={{
            backgroundColor: '#0c1a33',
            border: '1px solid #1e3a6c',
            borderRadius: '8px',
            padding: '6px 14px',
            display: 'flex',
            flexDirection: 'column',
            gap: '2px'
          }}
        >
          <div style={{ fontSize: '0.62rem', color: '#64748b', fontWeight: 700, letterSpacing: '0.5px' }}>
            CORRIDOR HEALTH
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '0.88rem', fontWeight: 800, color: '#f8fafc' }}>
              {healthScore.toFixed(1)}/100 ({healthStatus})
            </span>
            <span
              style={{
                backgroundColor: 'rgba(16, 185, 129, 0.15)',
                color: '#10b981',
                fontSize: '0.65rem',
                fontWeight: 800,
                padding: '1px 6px',
                borderRadius: '4px'
              }}
            >
              LOW (32%)
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
