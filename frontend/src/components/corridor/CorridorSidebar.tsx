import React from 'react';
import {
  LayoutDashboard,
  TrendingUp,
  Share2,
  Clock,
  AlertTriangle,
  BarChart2,
  FlaskConical,
  Bot,
  UserCheck,
  Users
} from 'lucide-react';

export type CorridorNavTab =
  | 'COMMAND_CENTER'
  | 'FORECAST'
  | 'NETWORK_VIEW'
  | 'DELAY_PROPAGATION'
  | 'JUNCTION_RISK'
  | 'TIME_SPACE'
  | 'WHAT_IF'
  | 'AI_EXPLAINER'
  | 'OPERATOR_VIEW'
  | 'PASSENGER_VIEW';

interface CorridorSidebarProps {
  activeTab: CorridorNavTab;
  onSelectTab: (tab: CorridorNavTab) => void;
}

export const CorridorSidebar: React.FC<CorridorSidebarProps> = ({ activeTab, onSelectTab }) => {
  const topNavItems = [
    { id: 'COMMAND_CENTER' as CorridorNavTab, label: 'Command Center', icon: LayoutDashboard },
    { id: 'FORECAST' as CorridorNavTab, label: 'Forecast', icon: TrendingUp },
    { id: 'NETWORK_VIEW' as CorridorNavTab, label: 'Network View', icon: Share2 },
    { id: 'DELAY_PROPAGATION' as CorridorNavTab, label: 'Delay Propagation', icon: Clock },
    { id: 'JUNCTION_RISK' as CorridorNavTab, label: 'Junction Risk', icon: AlertTriangle },
    { id: 'TIME_SPACE' as CorridorNavTab, label: 'Time-Space Chart', icon: BarChart2 },
    { id: 'WHAT_IF' as CorridorNavTab, label: 'What-If Lab', icon: FlaskConical },
    { id: 'AI_EXPLAINER' as CorridorNavTab, label: 'AI Explainer', icon: Bot },
  ];

  const bottomNavItems = [
    { id: 'OPERATOR_VIEW' as CorridorNavTab, label: 'Operator View', icon: UserCheck },
    { id: 'PASSENGER_VIEW' as CorridorNavTab, label: 'Passenger View', icon: Users },
  ];

  return (
    <aside
      style={{
        width: '210px',
        backgroundColor: '#070f1e',
        borderRight: '1px solid #14284b',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        flexShrink: 0,
        userSelect: 'none'
      }}
    >
      {/* Navigation Links */}
      <div style={{ padding: '16px 10px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {topNavItems.map((item) => {
          const isActive = activeTab === item.id;
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '9px 12px',
                borderRadius: '8px',
                border: 'none',
                backgroundColor: isActive ? '#0284c7' : 'transparent',
                color: isActive ? '#ffffff' : '#94a3b8',
                fontSize: '0.8rem',
                fontWeight: isActive ? 700 : 500,
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.15s ease-in-out',
                boxShadow: isActive ? '0 2px 10px rgba(2, 132, 199, 0.4)' : 'none'
              }}
            >
              <Icon size={16} color={isActive ? '#ffffff' : '#64748b'} />
              <span>{item.label}</span>
            </button>
          );
        })}

        {/* Divider */}
        <div style={{ height: '1px', backgroundColor: '#14284b', margin: '10px 4px' }} />

        {bottomNavItems.map((item) => {
          const isActive = activeTab === item.id;
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '9px 12px',
                borderRadius: '8px',
                border: 'none',
                backgroundColor: isActive ? '#0284c7' : 'transparent',
                color: isActive ? '#ffffff' : '#94a3b8',
                fontSize: '0.8rem',
                fontWeight: isActive ? 700 : 500,
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.15s ease-in-out',
                boxShadow: isActive ? '0 2px 10px rgba(2, 132, 199, 0.4)' : 'none'
              }}
            >
              <Icon size={16} color={isActive ? '#ffffff' : '#64748b'} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>

      {/* Footer Branding */}
      <div
        style={{
          padding: '16px 14px',
          borderTop: '1px solid #14284b',
          backgroundColor: '#050b17'
        }}
      >
        <div style={{ fontSize: '0.62rem', fontWeight: 800, color: '#38bdf8', letterSpacing: '0.5px' }}>
          PREDICT
        </div>
        <div style={{ fontSize: '0.62rem', fontWeight: 800, color: '#94a3b8', letterSpacing: '0.5px' }}>
          PREVENT
        </div>
        <div style={{ fontSize: '0.65rem', color: '#64748b', marginTop: '2px' }}>
          Enable Better Journeys
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            marginTop: '8px',
            fontSize: '0.65rem',
            color: '#94a3b8'
          }}
        >
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#0284c7' }} />
          <span>RailSutra • Indian Railways</span>
        </div>
      </div>
    </aside>
  );
};
