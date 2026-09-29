import React, { useState } from 'react';
import { Search, AlertTriangle, ShieldAlert, CheckCircle, Train, ChevronRight } from 'lucide-react';
import { RankedJunctionConflict, TrainState } from '../../types';

interface JunctionRiskViewProps {
  conflicts: RankedJunctionConflict[];
  trains: TrainState[];
  selectedTrainId: string;
  onSelectTrain: (trainId: string) => void;
  loading: boolean;
}

export const JunctionRiskView: React.FC<JunctionRiskViewProps> = ({
  conflicts,
  trains,
  selectedTrainId,
  onSelectTrain,
  loading
}) => {
  const [selectedJunctionIndex, setSelectedJunctionIndex] = useState<number>(0);
  const [trainFilter, setTrainFilter] = useState<'ALL' | 'LOW' | 'MEDIUM' | 'HIGH' | 'AFFECTED'>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  if (loading && conflicts.length === 0) {
    return (
      <div style={{ padding: '40px', color: '#94a3b8', textAlign: 'center' }}>
        Calculating real-time junction conflict indices...
      </div>
    );
  }

  const selectedJunction = conflicts[selectedJunctionIndex] || conflicts[0];

  // Filter trains for directory
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
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* 2-Column Section */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(340px, 1fr) minmax(380px, 1.2fr)', gap: '20px' }}>
        {/* Left Column: Ranked Corridor Junctions */}
        <div
          style={{
            backgroundColor: '#0c1a33',
            border: '1px solid #1e3a6c',
            borderRadius: '10px',
            padding: '18px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px'
          }}
        >
          <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#64748b', letterSpacing: '0.5px' }}>
            RANKED CORRIDOR JUNCTIONS (BY CONFLICT SCORE)
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '420px', overflowY: 'auto' }}>
            {conflicts.map((jn, index) => {
              const isSelected = index === selectedJunctionIndex;
              const isHigh = jn.risk_level === 'HIGH';
              const isMedium = jn.risk_level === 'MEDIUM';
              const badgeColor = isHigh ? '#f87171' : isMedium ? '#fbbf24' : '#10b981';
              const badgeBg = isHigh
                ? 'rgba(239, 68, 68, 0.15)'
                : isMedium
                ? 'rgba(245, 158, 11, 0.15)'
                : 'rgba(16, 185, 129, 0.15)';

              return (
                <div
                  key={jn.station_code || index}
                  onClick={() => setSelectedJunctionIndex(index)}
                  style={{
                    backgroundColor: isSelected ? '#0f274a' : '#081224',
                    border: `1px solid ${isSelected ? '#0284c7' : '#14284b'}`,
                    borderRadius: '8px',
                    padding: '12px 14px',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 800, color: '#f8fafc' }}>
                        {index + 1}. {jn.station_name}
                      </span>
                    </div>

                    <span
                      style={{
                        backgroundColor: badgeBg,
                        color: badgeColor,
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '0.65rem',
                        fontWeight: 800
                      }}
                    >
                      {jn.risk_level}
                    </span>
                  </div>

                  {/* Progress Bar */}
                  <div style={{ width: '100%', height: '4px', backgroundColor: '#1e293b', borderRadius: '2px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${Math.min(100, jn.conflict_score)}%`,
                        height: '100%',
                        backgroundColor: badgeColor,
                        borderRadius: '2px'
                      }}
                    />
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.7rem', color: '#64748b' }}>
                    <span>Conflict Score: {jn.conflict_score.toFixed(1)}/100</span>
                    <span>Approaching: {jn.approaching_trains_count} trains</span>
                    <span>~{jn.approaching_eta_min > 0 ? `${jn.approaching_eta_min.toFixed(1)} min` : 'Static'}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Why is this junction at risk? */}
        {selectedJunction && (
          <div
            style={{
              backgroundColor: '#0c1a33',
              border: '1px solid #1e3a6c',
              borderRadius: '10px',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px'
            }}
          >
            <div>
              <div style={{ fontSize: '0.65rem', fontWeight: 800, color: '#64748b', letterSpacing: '0.5px' }}>
                WHY IS THIS JUNCTION AT RISK?
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc', marginTop: '4px' }}>
                {selectedJunction.station_name}
              </div>
              <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
                Station ID: {selectedJunction.station_code} • Lat/Lon: {selectedJunction.lat?.toFixed(3) || '23.456'}, {selectedJunction.lng?.toFixed(3) || '75.412'}
              </div>
            </div>

            {/* Metrics */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div
                style={{
                  backgroundColor: '#081224',
                  border: '1px solid #14284b',
                  borderRadius: '8px',
                  padding: '14px'
                }}
              >
                <div style={{ fontSize: '0.65rem', color: '#64748b', fontWeight: 700 }}>
                  CONFLICT SCORE
                </div>
                <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fbbf24', marginTop: '4px' }}>
                  {selectedJunction.conflict_score.toFixed(1)}/100
                </div>
              </div>

              <div
                style={{
                  backgroundColor: '#081224',
                  border: '1px solid #14284b',
                  borderRadius: '8px',
                  padding: '14px'
                }}
              >
                <div style={{ fontSize: '0.65rem', color: '#64748b', fontWeight: 700 }}>
                  EXPECTED DELAY IMPACT
                </div>
                <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#38bdf8', marginTop: '4px' }}>
                  {selectedJunction.expected_impact_window_min}
                </div>
              </div>
            </div>

            {/* Factor Breakdown */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ fontSize: '0.68rem', fontWeight: 800, color: '#64748b', letterSpacing: '0.5px' }}>
                FACTOR BREAKDOWN:
              </div>

              {/* Factor 1: Converging Traffic Density */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#cbd5e1', marginBottom: '4px' }}>
                  <span>Converging Traffic Density</span>
                  <span>{selectedJunction.factor_breakdown.converging_traffic_density_pct}%</span>
                </div>
                <div style={{ width: '100%', height: '5px', backgroundColor: '#1e293b', borderRadius: '3px' }}>
                  <div
                    style={{
                      width: `${selectedJunction.factor_breakdown.converging_traffic_density_pct}%`,
                      height: '100%',
                      backgroundColor: '#38bdf8',
                      borderRadius: '3px'
                    }}
                  />
                </div>
              </div>

              {/* Factor 2: Approach Track Congestion */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#cbd5e1', marginBottom: '4px' }}>
                  <span>Approach Track Congestion</span>
                  <span>{selectedJunction.factor_breakdown.approach_track_congestion_pct}%</span>
                </div>
                <div style={{ width: '100%', height: '5px', backgroundColor: '#1e293b', borderRadius: '3px' }}>
                  <div
                    style={{
                      width: `${selectedJunction.factor_breakdown.approach_track_congestion_pct}%`,
                      height: '100%',
                      backgroundColor: '#fbbf24',
                      borderRadius: '3px'
                    }}
                  />
                </div>
              </div>

              {/* Factor 3: Priority Clearance Precedence */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#cbd5e1', marginBottom: '4px' }}>
                  <span>Priority Clearance Precedence</span>
                  <span>{selectedJunction.factor_breakdown.priority_clearance_precedence_pct}%</span>
                </div>
                <div style={{ width: '100%', height: '5px', backgroundColor: '#1e293b', borderRadius: '3px' }}>
                  <div
                    style={{
                      width: `${selectedJunction.factor_breakdown.priority_clearance_precedence_pct}%`,
                      height: '100%',
                      backgroundColor: '#2dd4bf',
                      borderRadius: '3px'
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Affected Services */}
            <div>
              <div style={{ fontSize: '0.68rem', fontWeight: 800, color: '#64748b', letterSpacing: '0.5px', marginBottom: '8px' }}>
                AFFECTED SERVICES:
              </div>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {selectedJunction.affected_services.map((svc) => (
                  <span
                    key={svc.train_number}
                    onClick={() => onSelectTrain(svc.train_number)}
                    style={{
                      backgroundColor: svc.train_id === selectedTrainId || svc.train_number === selectedTrainId.replace('TRAIN_', '')
                        ? '#0284c7'
                        : '#081224',
                      color: '#ffffff',
                      border: '1px solid #1e3a6c',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      cursor: 'pointer'
                    }}
                  >
                    {svc.train_number} ({svc.train_name.split(' ')[0]})
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Corridor Train Directory (Image 3 & 5 Bottom) */}
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
            {/* Search Box */}
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

            {/* Filter Pills */}
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

        {/* Train Table */}
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
                const isSelected = t.train_id === selectedTrainId || t.train_number === selectedTrainId.replace('TRAIN_', '');
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
                      {t.next_station_id || 'En Route'}
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
