import React, { useState, useEffect } from 'react';
import { Play, Pause, RotateCcw, ChevronDown, Clock, AlertTriangle, ArrowDown } from 'lucide-react';
import { DownstreamPropagationResponse } from '../../types';

interface DelayPropagationViewProps {
  data: DownstreamPropagationResponse | null;
  loading: boolean;
}

export const DelayPropagationView: React.FC<DelayPropagationViewProps> = ({ data, loading }) => {
  const [activeStep, setActiveStep] = useState<number>(999);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  useEffect(() => {
    let timer: any;
    if (isPlaying && data && data.propagation_chain.length > 0) {
      timer = setInterval(() => {
        setActiveStep((prev) => {
          if (prev >= data.propagation_chain.length) {
            setIsPlaying(false);
            return data.propagation_chain.length;
          }
          return prev + 1;
        });
      }, 1200);
    }
    return () => clearInterval(timer);
  }, [isPlaying, data]);

  const handlePlay = () => {
    setActiveStep(1);
    setIsPlaying(true);
  };

  const handlePause = () => {
    setIsPlaying(false);
  };

  const handleReset = () => {
    setIsPlaying(false);
    setActiveStep(999);
  };

  if (loading || !data) {
    return (
      <div style={{ padding: '40px', color: '#94a3b8', textAlign: 'center' }}>
        Evaluating downstream headway delay propagation...
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top 4 KPI Cards (Image 2) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '16px' }}>
        {/* Card 1: Source Train Delay */}
        <div
          style={{
            backgroundColor: '#0c1a33',
            border: '1px solid #1e3a6c',
            borderRadius: '10px',
            padding: '16px 20px'
          }}
        >
          <div style={{ fontSize: '0.65rem', fontWeight: 700, color: '#64748b', letterSpacing: '0.5px' }}>
            SOURCE TRAIN DELAY
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#fbbf24', margin: '6px 0 2px 0' }}>
            +{data.source_delay_minutes.toFixed(1)} min
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {data.source_train_number} — {data.source_train_name}
          </div>
        </div>

        {/* Card 2: Critical Junction Conflict */}
        <div
          style={{
            backgroundColor: '#0c1a33',
            border: '1px solid #1e3a6c',
            borderRadius: '10px',
            padding: '16px 20px'
          }}
        >
          <div style={{ fontSize: '0.65rem', fontWeight: 700, color: '#64748b', letterSpacing: '0.5px' }}>
            CRITICAL JUNCTION CONFLICT
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f87171', margin: '8px 0 2px 0', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {data.critical_junction_name}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
            Conflict Score: {data.critical_conflict_score.toFixed(1)}/100
          </div>
        </div>

        {/* Card 3: Downstream Exposed Services */}
        <div
          style={{
            backgroundColor: '#0c1a33',
            border: '1px solid #1e3a6c',
            borderRadius: '10px',
            padding: '16px 20px'
          }}
        >
          <div style={{ fontSize: '0.65rem', fontWeight: 700, color: '#64748b', letterSpacing: '0.5px' }}>
            DOWNSTREAM EXPOSED SERVICES
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#38bdf8', margin: '6px 0 2px 0' }}>
            {data.downstream_exposed_services_count} Services
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
            Services sharing bottleneck section
          </div>
        </div>

        {/* Card 4: Total Induced Network Delay */}
        <div
          style={{
            backgroundColor: '#0c1a33',
            border: '1px solid #1e3a6c',
            borderRadius: '10px',
            padding: '16px 20px'
          }}
        >
          <div style={{ fontSize: '0.65rem', fontWeight: 700, color: '#64748b', letterSpacing: '0.5px' }}>
            TOTAL INDUCED NETWORK DELAY
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#f87171', margin: '6px 0 2px 0' }}>
            +{data.total_induced_network_delay_minutes.toFixed(1)} min
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
            Cascading network penalty
          </div>
        </div>
      </div>

      {/* Animation & Action Controls Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: '#091326',
          border: '1px solid #1e3a6c',
          borderRadius: '8px',
          padding: '10px 16px',
          flexWrap: 'wrap',
          gap: '12px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={handlePlay}
            disabled={isPlaying}
            style={{
              backgroundColor: '#0284c7',
              border: 'none',
              color: 'white',
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '0.75rem',
              fontWeight: 700,
              cursor: isPlaying ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              opacity: isPlaying ? 0.6 : 1
            }}
          >
            <Play size={13} />
            <span>PLAY CASCADE ANIMATION</span>
          </button>

          <button
            onClick={handlePause}
            disabled={!isPlaying}
            style={{
              backgroundColor: '#0c1a33',
              border: '1px solid #1e3a6c',
              color: '#94a3b8',
              padding: '6px 12px',
              borderRadius: '6px',
              fontSize: '0.75rem',
              fontWeight: 700,
              cursor: !isPlaying ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Pause size={13} />
            <span>PAUSE</span>
          </button>

          <button
            onClick={handleReset}
            style={{
              backgroundColor: '#0c1a33',
              border: '1px solid #1e3a6c',
              color: '#94a3b8',
              padding: '6px 12px',
              borderRadius: '6px',
              fontSize: '0.75rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <RotateCcw size={13} />
            <span>RESET</span>
          </button>
        </div>

        <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
          Status: <span style={{ color: isPlaying ? '#38bdf8' : '#10b981', fontWeight: 700 }}>{isPlaying ? 'Cascading...' : 'Ready'}</span>
        </div>
      </div>

      {/* Propagation Chain Reaction Flow (Image 2) */}
      <div
        style={{
          backgroundColor: '#0c1a33',
          border: '1px solid #1e3a6c',
          borderRadius: '10px',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px'
        }}
      >
        <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#64748b', letterSpacing: '0.5px' }}>
          PROPAGATION CHAIN REACTION FLOW
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {data.propagation_chain.map((item, index) => {
            const isVisible = index < activeStep;
            const isJunction = item.type === 'JUNCTION_BOTTLENECK';

            return (
              <React.Fragment key={index}>
                {index > 0 && (
                  <div style={{ display: 'flex', justifyContent: 'center', margin: '2px 0', opacity: isVisible ? 1 : 0.2 }}>
                    <div
                      style={{
                        width: '0',
                        height: '0',
                        borderLeft: '5px solid transparent',
                        borderRight: '5px solid transparent',
                        borderTop: '6px solid #334155'
                      }}
                    />
                  </div>
                )}

                <div
                  style={{
                    backgroundColor: isJunction ? '#0b1930' : '#081224',
                    border: `1px solid ${isJunction ? '#1e3a6c' : '#14284b'}`,
                    borderRadius: '8px',
                    padding: '12px 18px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    opacity: isVisible ? 1 : 0.3,
                    transition: 'all 0.3s ease-in-out',
                    transform: isVisible ? 'translateY(0)' : 'translateY(4px)'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div
                      style={{
                        backgroundColor: isJunction ? '#0284c7' : '#1e293b',
                        color: isJunction ? '#ffffff' : '#38bdf8',
                        width: '26px',
                        height: '26px',
                        borderRadius: '6px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.75rem',
                        fontWeight: 800,
                        flexShrink: 0
                      }}
                    >
                      {isJunction ? 'JN' : item.step}
                    </div>

                    <div>
                      <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc' }}>
                        {item.title}
                      </div>
                      <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
                        {item.subtitle}
                      </div>
                    </div>
                  </div>

                  {/* Delay Display / Badge */}
                  <div>
                    {isJunction ? (
                      <span
                        style={{
                          backgroundColor: 'rgba(245, 158, 11, 0.15)',
                          color: '#fbbf24',
                          border: '1px solid rgba(245, 158, 11, 0.3)',
                          padding: '4px 10px',
                          borderRadius: '4px',
                          fontSize: '0.72rem',
                          fontWeight: 800
                        }}
                      >
                        {item.risk_badge}
                      </span>
                    ) : (
                      <span style={{ fontSize: '1.05rem', fontWeight: 800, color: '#fbbf24' }}>
                        {item.delay_display}
                      </span>
                    )}
                  </div>
                </div>
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
};
