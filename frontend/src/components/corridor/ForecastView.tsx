import React from 'react';
import { TrainETAComparison, TrajectoryPoint } from '../../types';

interface ForecastViewProps {
  data: TrainETAComparison | null;
  loading: boolean;
}

export const ForecastView: React.FC<ForecastViewProps> = ({ data, loading }) => {
  if (loading || !data) {
    return (
      <div style={{ padding: '40px', color: '#94a3b8', textAlign: 'center' }}>
        Loading dynamic ETA forecast telemetry...
      </div>
    );
  }

  const points = data.trajectory_band || [];

  // SVG dimensions
  const svgWidth = 960;
  const svgHeight = 360;
  const paddingX = 80;
  const paddingY = 40;
  const chartWidth = svgWidth - paddingX * 2;
  const chartHeight = svgHeight - paddingY * 2;

  // Max delay for Y-axis scale
  const maxDelayVal = Math.max(
    30,
    ...points.map((p) => Math.max(p.proactive_delay_min, p.p90_delay_min, p.reactive_delay_min))
  );

  const getX = (index: number) => {
    if (points.length <= 1) return paddingX + chartWidth / 2;
    return paddingX + (index / (points.length - 1)) * chartWidth;
  };

  const getY = (delayMin: number) => {
    const clamped = Math.max(0, Math.min(delayMin, maxDelayVal));
    return svgHeight - paddingY - (clamped / maxDelayVal) * chartHeight;
  };

  // Build SVG path for scheduled line (delay = 0)
  const schedPath = `M ${getX(0)} ${getY(0)} L ${getX(points.length - 1)} ${getY(0)}`;

  // Reactive line
  const reactivePath = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p.reactive_delay_min)}`)
    .join(' ');

  // Proactive path
  const proactivePath = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p.proactive_delay_min)}`)
    .join(' ');

  // Uncertainty band polygon (P10 to P90)
  const topBand = points.map((p, i) => `${getX(i)},${getY(p.p90_delay_min)}`).join(' ');
  const bottomBand = points
    .slice()
    .reverse()
    .map((p, i) => `${getX(points.length - 1 - i)},${getY(p.p10_delay_min)}`)
    .join(' ');
  const bandPolygon = `${topBand} ${bottomBand}`;

  // Find bottleneck point
  const conflictIdx = points.findIndex((p) => p.is_conflict_point) !== -1
    ? points.findIndex((p) => p.is_conflict_point)
    : Math.floor(points.length / 2);

  const conflictPoint = points[conflictIdx] || points[0];

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Subtitle */}
      <div>
        <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
          Mathematical deconstruction of dynamic corridor delay forecasting versus linear reactive tracking.
        </div>
      </div>

      {/* 4 Top Metric Cards (Image 4) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '16px' }}>
        {/* Card 1: Scheduled Master Timetable */}
        <div
          style={{
            backgroundColor: '#0c1a33',
            border: '1px solid #1e3a6c',
            borderRadius: '10px',
            padding: '16px 20px'
          }}
        >
          <div style={{ fontSize: '0.65rem', fontWeight: 700, color: '#64748b', letterSpacing: '0.5px' }}>
            SCHEDULED MASTER TIMETABLE
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#f8fafc', margin: '8px 0 4px 0' }}>
            {data.scheduled_timetable_eta}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
            Planned arrival time at terminal destination
          </div>
        </div>

        {/* Card 2: Current Reactive Estimate */}
        <div
          style={{
            backgroundColor: '#0c1a33',
            border: '1px solid #1e3a6c',
            borderRadius: '10px',
            padding: '16px 20px'
          }}
        >
          <div style={{ fontSize: '0.65rem', fontWeight: 700, color: '#64748b', letterSpacing: '0.5px' }}>
            CURRENT REACTIVE ESTIMATE
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#fbbf24', margin: '8px 0 4px 0' }}>
            {data.current_reactive_estimate.split(' ')[0]}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#fbbf24', fontWeight: 600 }}>
            +{data.current_delay_minutes.toFixed(0)} min current delay
          </div>
        </div>

        {/* Card 3: RailSutra Proactive Forecast (Highlighted in Cyan) */}
        <div
          style={{
            backgroundColor: 'rgba(2, 132, 199, 0.08)',
            border: '1.5px solid #0284c7',
            borderRadius: '10px',
            padding: '16px 20px',
            boxShadow: '0 0 16px rgba(2, 132, 199, 0.2)'
          }}
        >
          <div style={{ fontSize: '0.65rem', fontWeight: 800, color: '#38bdf8', letterSpacing: '0.5px' }}>
            RAILSUTRA PROACTIVE FORECAST
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#38bdf8', margin: '8px 0 4px 0' }}>
            {data.proactive_forecast_eta.split(' ')[0]}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#38bdf8', fontWeight: 700 }}>
            +{data.proactive_delay_minutes.toFixed(0)} min proactive forecast
          </div>
        </div>

        {/* Card 4: Prediction Uncertainty Interval */}
        <div
          style={{
            backgroundColor: '#0c1a33',
            border: '1px solid #1e3a6c',
            borderRadius: '10px',
            padding: '16px 20px'
          }}
        >
          <div style={{ fontSize: '0.65rem', fontWeight: 700, color: '#64748b', letterSpacing: '0.5px' }}>
            PREDICTION UNCERTAINTY INTERVAL
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#38bdf8', margin: '8px 0 4px 0' }}>
            {data.uncertainty_interval}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
            {data.forecast_confidence_pct.toFixed(1)}% forecast confidence
          </div>
        </div>
      </div>

      {/* Main Trajectory Chart (Image 4) */}
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
        <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#64748b', letterSpacing: '0.5px' }}>
          PROJECTED CORRIDOR TRAJECTORY & UNCERTAINTY BAND
        </div>

        {/* SVG Curve Plot */}
        <div style={{ width: '100%', overflowX: 'auto' }}>
          <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} style={{ width: '100%', height: 'auto', minWidth: '700px' }}>
            <defs>
              <linearGradient id="bandGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#0284c7" stopOpacity="0.05" />
              </linearGradient>
            </defs>

            {/* Grid horizontal lines */}
            {[0, 5, 10, 15, 20, 25].map((val) => {
              const y = getY(val);
              return (
                <g key={val}>
                  <line
                    x1={paddingX}
                    y1={y}
                    x2={svgWidth - paddingX}
                    y2={y}
                    stroke="rgba(255, 255, 255, 0.06)"
                    strokeDasharray="4 4"
                  />
                  <text
                    x={paddingX - 10}
                    y={y + 4}
                    textAnchor="end"
                    fill="#64748b"
                    fontSize="10"
                    fontFamily="monospace"
                  >
                    +{val}m
                  </text>
                </g>
              );
            })}

            {/* Uncertainty Band Polygon */}
            {points.length > 1 && (
              <polygon points={bandPolygon} fill="url(#bandGrad)" />
            )}

            {/* Scheduled Timetable Path (Dashed Grey) */}
            <path
              d={schedPath}
              fill="none"
              stroke="#64748b"
              strokeWidth="2"
              strokeDasharray="6 4"
            />

            {/* Current Reactive Extrapolation (Amber) */}
            <path
              d={reactivePath}
              fill="none"
              stroke="#fbbf24"
              strokeWidth="2.5"
            />

            {/* RailSutra Proactive Projected Path (Cyan) */}
            <path
              d={proactivePath}
              fill="none"
              stroke="#38bdf8"
              strokeWidth="3"
            />

            {/* Station X-Axis Markers & Labels */}
            {points.map((p, i) => {
              const x = getX(i);
              return (
                <g key={i}>
                  <line
                    x1={x}
                    y1={svgHeight - paddingY}
                    x2={x}
                    y2={svgHeight - paddingY + 6}
                    stroke="#334155"
                    strokeWidth="1.5"
                  />
                  <text
                    x={x}
                    y={svgHeight - paddingY + 22}
                    textAnchor="middle"
                    fill="#94a3b8"
                    fontSize="10"
                    fontWeight="600"
                  >
                    {p.station_name}
                  </text>
                  <text
                    x={x}
                    y={svgHeight - paddingY + 34}
                    textAnchor="middle"
                    fill="#64748b"
                    fontSize="9"
                  >
                    ({p.distance_km.toFixed(0)} km)
                  </text>
                </g>
              );
            })}

            {/* Bottleneck Convergence Callout (Nagda Jn) */}
            {conflictPoint && (
              <g>
                <circle
                  cx={getX(conflictIdx)}
                  cy={getY(conflictPoint.proactive_delay_min)}
                  r="6"
                  fill="#fbbf24"
                  stroke="#ffffff"
                  strokeWidth="2"
                />
                <rect
                  x={getX(conflictIdx) - 80}
                  y={getY(conflictPoint.proactive_delay_min) - 34}
                  width="160"
                  height="22"
                  rx="4"
                  fill="#0f172a"
                  stroke="#fbbf24"
                  strokeWidth="1"
                />
                <text
                  x={getX(conflictIdx)}
                  y={getY(conflictPoint.proactive_delay_min) - 19}
                  textAnchor="middle"
                  fill="#fbbf24"
                  fontSize="9.5"
                  fontWeight="700"
                >
                  Nagda Bottleneck Convergence
                </text>
              </g>
            )}

            {/* Terminal Points Callout */}
            {points.length > 0 && (
              <g>
                {/* Proactive Terminal Node */}
                <circle
                  cx={getX(points.length - 1)}
                  cy={getY(points[points.length - 1].proactive_delay_min)}
                  r="5"
                  fill="#ffffff"
                  stroke="#38bdf8"
                  strokeWidth="2"
                />
                <text
                  x={getX(points.length - 1) + 10}
                  y={getY(points[points.length - 1].proactive_delay_min) - 4}
                  fill="#38bdf8"
                  fontSize="11"
                  fontWeight="800"
                >
                  RailSutra: {data.proactive_forecast_eta.split(' ')[0]}
                </text>
                <text
                  x={getX(points.length - 1) + 10}
                  y={getY(points[points.length - 1].proactive_delay_min) + 10}
                  fill="#94a3b8"
                  fontSize="9.5"
                >
                  Band: [{data.uncertainty_interval}]
                </text>

                {/* Reactive Terminal Node */}
                <circle
                  cx={getX(points.length - 1)}
                  cy={getY(points[points.length - 1].reactive_delay_min)}
                  r="4"
                  fill="#fbbf24"
                />
                <text
                  x={getX(points.length - 1) + 10}
                  y={getY(points[points.length - 1].reactive_delay_min) + 4}
                  fill="#fbbf24"
                  fontSize="10"
                  fontWeight="700"
                >
                  Reactive GPS: {data.current_reactive_estimate.split(' ')[0]}
                </text>

                {/* Timetable Terminal Node */}
                <text
                  x={getX(points.length - 1) + 10}
                  y={getY(0) + 4}
                  fill="#64748b"
                  fontSize="10"
                >
                  Timetable: {data.scheduled_timetable_eta}
                </text>
              </g>
            )}
          </svg>
        </div>

        {/* Legend */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '24px',
            borderTop: '1px solid #1e3a6c',
            paddingTop: '14px',
            flexWrap: 'wrap',
            fontSize: '0.75rem'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#94a3b8' }}>
            <span style={{ width: '20px', height: '2px', borderTop: '2px dashed #64748b' }} />
            <span>Scheduled Timetable Path</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#fbbf24' }}>
            <span style={{ width: '20px', height: '2.5px', backgroundColor: '#fbbf24' }} />
            <span>Current Reactive Extrapolation</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#38bdf8', fontWeight: 700 }}>
            <span style={{ width: '20px', height: '3px', backgroundColor: '#38bdf8' }} />
            <span>RailSutra Proactive Projected Path</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#38bdf8' }}>
            <span
              style={{
                width: '16px',
                height: '10px',
                backgroundColor: 'rgba(56, 189, 248, 0.25)',
                border: '1px solid #38bdf8'
              }}
            />
            <span>Confidence Uncertainty Band</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#fbbf24' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#fbbf24' }} />
            <span>Predicted Conflict Point</span>
          </div>
        </div>
      </div>
    </div>
  );
};
