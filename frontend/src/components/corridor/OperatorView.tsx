import React, { useState } from 'react';
import { Search, ShieldAlert, AlertTriangle, Info, CheckCircle2, ChevronRight } from 'lucide-react';
import { TrainState, RankedJunctionConflict, TrainETAComparison } from '../../types';

interface OperatorViewProps {
  trains: TrainState[];
  selectedTrain: TrainState | null;
  selectedTrainETA: TrainETAComparison | null;
  conflicts: RankedJunctionConflict[];
  onSelectTrain: (trainId: string) => void;
}

export const OperatorView: React.FC<OperatorViewProps> = ({
  trains,
  selectedTrain,
  selectedTrainETA,
  conflicts,
  onSelectTrain
}) => {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [trainFilter, setTrainFilter] = useState<'ALL' | 'LOW' | 'MEDIUM' | 'HIGH' | 'AFFECTED'>('ALL');

  const topConflict = conflicts[0];

  const sourceTrainName = selectedTrain
    ? `${selectedTrain.train_number} — ${selectedTrain.train_name}`
    : '12926 — Paschim Superfast Express';

  const sourceDelay = selectedTrain ? selectedTrain.current_delay_minutes : 9.0;
  const speed = selectedTrain?.speed_kmh || 82.0;
  const proactiveEta = selectedTrainETA?.proactive_forecast_eta?.split(' ')[0] || '15:07';

  const criticalJnName = topConflict ? topConflict.station_name : 'Nagda Jn';
  const criticalJnScore = topConflict ? topConflict.conflict_score : 46.9;
  const criticalJnRisk = topConflict ? topConflict.risk_level : 'MEDIUM';
  const impactWindow = topConflict ? topConflict.expected_impact_window_min : '7–16.4 min';

  const filteredTrains = trains.filter((t) => {
    const q = searchQuery.toLowerCase().trim();
    const matchSearch =
      !q ||
      t.train_number.toLowerCase().includes(q) ||
      t.train_name.toLowerCase().includes(q) ||
      t.origin_station_name?.toLowerCase().includes(q) ||
      t.destination_station_name?.toLowerCase().includes(q);

    if (!matchSearch) return false;

    const delay = t.current_delay_minutes;
    const risk = delay >= 30 ? 'HIGH' : delay >= 15 ? 'MEDIUM' : 'LOW';

    if (trainFilter === 'ALL') return true;
    if (trainFilter === 'LOW') return risk === 'LOW';
    if (trainFilter === 'MEDIUM') return risk === 'MEDIUM';
    if (trainFilter === 'HIGH') return risk === 'HIGH';
    if (trainFilter === 'AFFECTED') return delay > 5;
    return true;
  });

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Title & Subtitle */}
      <div>
        <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc' }}>
          Corridor Section Controller & Dispatch Decision Support
        </div>
        <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '2px' }}>
          Tactical decision support view for section controllers to anticipate bottlenecks and prioritize clearance headway.
        </div>
      </div>

      {/* 3 Top Advisory Cards (Image 5) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        {/* Card 1: Highest-Priority Conflict Service */}
        <div
          style={{
            backgroundColor: '#0c1a33',
            border: '1px solid #1e3a6c',
            borderRadius: '10px',
            padding: '18px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}
        >
          <div style={{ fontSize: '0.65rem', fontWeight: 800, color: '#64748b', letterSpacing: '0.5px' }}>
            HIGHEST-PRIORITY CONFLICT SERVICE
          </div>
          <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#f8fafc' }}>
            {sourceTrainName}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
            Speed: {speed.toFixed(0)} km/h • Current Delay: +{sourceDelay.toFixed(0)} min • RailSutra ETA: {proactiveEta}
          </div>
          <div
            style={{
              marginTop: '6px',
              fontSize: '0.72rem',
              color: '#38bdf8',
              backgroundColor: 'rgba(56, 189, 248, 0.08)',
              border: '1px solid rgba(56, 189, 248, 0.2)',
              padding: '8px 12px',
              borderRadius: '6px'
            }}
          >
            <strong>Advisory:</strong> Give priority signal clearance approaching {criticalJnName} to prevent downstream absorption delay.
          </div>
        </div>

        {/* Card 2: Critical Corridor Bottleneck */}
        <div
          style={{
            backgroundColor: '#0c1a33',
            border: '1px solid #1e3a6c',
            borderRadius: '10px',
            padding: '18px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}
        >
          <div style={{ fontSize: '0.65rem', fontWeight: 800, color: '#64748b', letterSpacing: '0.5px' }}>
            CRITICAL CORRIDOR BOTTLENECK
          </div>
          <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#fbbf24' }}>
            {criticalJnName} ({criticalJnRisk} RISK)
          </div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
            Conflict score {criticalJnScore.toFixed(1)}/100 with {topConflict?.approaching_trains_count || 2} converging train movements within headway threshold.
          </div>
          <div
            style={{
              marginTop: '6px',
              fontSize: '0.72rem',
              color: '#fbbf24',
              backgroundColor: 'rgba(245, 158, 11, 0.08)',
              border: '1px solid rgba(245, 158, 11, 0.2)',
              padding: '8px 12px',
              borderRadius: '6px'
            }}
          >
            Expected impact window: {impactWindow}. Recommended clearance stagger.
          </div>
        </div>

        {/* Card 3: Decision Support Advisory (Auditable Disclaimer) */}
        <div
          style={{
            backgroundColor: '#0c1a33',
            border: '1px solid #1e3a6c',
            borderRadius: '10px',
            padding: '18px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}
        >
          <div style={{ fontSize: '0.65rem', fontWeight: 800, color: '#64748b', letterSpacing: '0.5px' }}>
            DECISION SUPPORT ADVISORY
          </div>
          <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#f8fafc' }}>
            Dispatch Guidance
          </div>
          <div
            style={{
              fontSize: '0.74rem',
              color: '#cbd5e1',
              lineHeight: '1.4',
              backgroundColor: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid #1e3a6c',
              padding: '8px 12px',
              borderRadius: '6px'
            }}
          >
            RailSutra provides predictive decision support to human operators. It does not autonomously route, dispatch, or signal trains.
          </div>
          <div style={{ fontSize: '0.72rem', color: '#10b981', fontWeight: 700, marginTop: '2px' }}>
            System Status: Active Monitoring
          </div>
        </div>
      </div>

      {/* Corridor Train Directory (Image 5 Bottom) */}
      <div
        style={{
          backgroundColor: '#0c1a33',
          border: '1px solid #1e3a6c',
          borderRadius: '10px',
          padding: '18px',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '0.5px' }}>
              CORRIDOR TRAIN DIRECTORY <span style={{ color: '#64748b', fontWeight: 500 }}>(Click any train row to switch global intelligence context)</span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            {/* Search Input */}
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <input
                type="text"
                placeholder="Search train number, name, or station..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  backgroundColor: '#081224',
                  border: '1px solid #1e3a6c',
                  color: '#f8fafc',
                  padding: '5px 10px 5px 28px',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  width: '240px',
                  outline: 'none'
                }}
              />
              <Search size={12} color="#64748b" style={{ position: 'absolute', left: '8px' }} />
            </div>

            {/* Filter Buttons */}
            <div style={{ display: 'flex', gap: '4px' }}>
              {(['ALL', 'LOW', 'MEDIUM', 'HIGH', 'AFFECTED'] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setTrainFilter(mode)}
                  style={{
                    backgroundColor: trainFilter === mode ? '#0284c7' : '#081224',
                    border: '1px solid #1e3a6c',
                    color: trainFilter === mode ? '#ffffff' : '#94a3b8',
                    padding: '4px 10px',
                    borderRadius: '4px',
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    cursor: 'pointer'
                  }}
                >
                  {mode === 'ALL' ? `ALL (${trains.length})` : mode}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Table matching Image 5 */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #1e3a6c', color: '#64748b', textAlign: 'left' }}>
                <th style={{ padding: '8px 12px' }}>TRAIN</th>
                <th style={{ padding: '8px 12px' }}>TYPE</th>
                <th style={{ padding: '8px 12px' }}>CURRENT LOCATION</th>
                <th style={{ padding: '8px 12px' }}>CURRENT DELAY</th>
                <th style={{ padding: '8px 12px' }}>PREDICTED ETA</th>
                <th style={{ padding: '8px 12px' }}>EXPECTED DELAY</th>
                <th style={{ padding: '8px 12px' }}>RISK LEVEL</th>
                <th style={{ padding: '8px 12px' }}>NEXT CRITICAL POINT</th>
              </tr>
            </thead>
            <tbody>
              {filteredTrains.map((t) => {
                const isSelected = selectedTrain?.train_number === t.train_number;
                const curDel = t.current_delay_minutes;
                const risk = curDel >= 30 ? 'HIGH' : curDel >= 15 ? 'MEDIUM' : 'LOW';
                const badgeColor = risk === 'HIGH' ? '#f87171' : risk === 'MEDIUM' ? '#fbbf24' : '#10b981';

                return (
                  <tr
                    key={t.train_id}
                    onClick={() => onSelectTrain(t.train_number)}
                    style={{
                      borderBottom: '1px solid #14284b',
                      backgroundColor: isSelected ? 'rgba(2, 132, 199, 0.15)' : 'transparent',
                      cursor: 'pointer',
                      transition: 'background 0.15s'
                    }}
                  >
                    <td style={{ padding: '10px 12px', fontWeight: 700, color: isSelected ? '#38bdf8' : '#f8fafc' }}>
                      {t.train_number} — {t.train_name}
                    </td>
                    <td style={{ padding: '10px 12px', color: '#94a3b8' }}>
                      {t.train_type}
                    </td>
                    <td style={{ padding: '10px 12px', color: '#38bdf8' }}>
                      {t.next_station_id || 'ST05'}
                    </td>
                    <td style={{ padding: '10px 12px', color: curDel > 0 ? '#fbbf24' : '#10b981', fontWeight: 700 }}>
                      +{curDel.toFixed(0)} min
                    </td>
                    <td style={{ padding: '10px 12px', color: '#f8fafc', fontWeight: 700 }}>
                      {t.current_eta?.dynamic_forecast_eta?.split(' ')[0] || '--:--'}
                    </td>
                    <td style={{ padding: '10px 12px', color: '#fbbf24' }}>
                      +{(curDel + 8).toFixed(0)} min
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <span
                        style={{
                          backgroundColor: 'rgba(255, 255, 255, 0.05)',
                          color: badgeColor,
                          border: `1px solid ${badgeColor}40`,
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '0.68rem',
                          fontWeight: 700
                        }}
                      >
                        {risk}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', color: '#94a3b8' }}>
                      Approach Jct
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
