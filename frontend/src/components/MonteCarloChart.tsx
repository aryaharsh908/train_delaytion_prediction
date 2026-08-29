import React from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface MonteCarloChartProps {
  samples: number[];
}

export const MonteCarloChart: React.FC<MonteCarloChartProps> = ({ samples }) => {
  if (!samples || samples.length === 0) return null;

  // Build histogram frequency data
  const sorted = [...samples].sort((a, b) => a - b);
  const minVal = Math.floor(sorted[0]);
  const maxVal = Math.ceil(sorted[sorted.length - 1]);
  const step = Math.max(1, Math.ceil((maxVal - minVal) / 8));

  const bins: { delay: string; count: number }[] = [];
  for (let b = minVal; b <= maxVal; b += step) {
    const count = samples.filter((s) => s >= b && s < b + step).length;
    bins.push({ delay: `+${b}m`, count });
  }

  return (
    <div style={{ width: '100%', height: '140px', marginTop: '10px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={bins} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="mcGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.6} />
              <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="delay" stroke="#64748b" fontSize={10} tickLine={false} />
          <YAxis stroke="#64748b" fontSize={10} tickLine={false} />
          <Tooltip
            contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', fontSize: '0.75rem' }}
          />
          <Area type="monotone" dataKey="count" stroke="#38bdf8" strokeWidth={2} fillOpacity={1} fill="url(#mcGradient)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
