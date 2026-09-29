import React, { useState, useEffect } from 'react';
import { Zap, ArrowRight, RefreshCw, AlertTriangle, Layers } from 'lucide-react';
import { CounterfactualResponse, TrainState } from '../../types';
import { runCorridorCounterfactual } from '../../services/api';

interface WhatIfLabViewProps {
  selectedTrain: TrainState | null;
  trains: TrainState[];
  onSelectTrain: (trainId: string) => void;
}

export const WhatIfLabView: React.FC<WhatIfLabViewProps> = ({
  selectedTrain,
  trains,
  onSelectTrain
}) => {
  const [injectedDelay, setInjectedDelay] = useState<number>(10);
  const [simulationResult, setSimulationResult] = useState<CounterfactualResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const cleanTrainNum = selectedTrain?.train_number || '12926';

  const executeSimulation = async (delayVal?: number) => {
    const d = delayVal !== undefined ? delayVal : injectedDelay;
    setLoading(true);
    try {
      const res = await runCorridorCounterfactual({
        train_number: cleanTrainNum,
        train_id: `TRAIN_${cleanTrainNum}`,
        intervention_type: 'INJECT_DELAY',
        injected_delay_minutes: d
      });
      setSimulationResult(res);
    } catch (err) {
      console.error('Counterfactual simulation failed:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    executeSimulation();
  }, [cleanTrainNum]);

  const handleQuickAdd = (minutes: number) => {
    setInjectedDelay(minutes);
    executeSimulation(minutes);
  };

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Header */}
      <div>
        <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc' }}>
          What-If Operations Lab
        </div>
        <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '2px' }}>
          Simulate an additional delay perturbation on any train and observe how the corridor and downstream services respond.
        </div>
      </div>

      {/* Control Configuration Bar (Image 1) */}
      <div
        style={{
          backgroundColor: '#0c1a33',
          border: '1px solid #1e3a6c',
          borderRadius: '10px',
          padding: '16px 20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px'
        }}
      >
        {/* Selected Service */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <span style={{ fontSize: '0.65rem', fontWeight: 800, color: '#64748b', letterSpacing: '0.5px' }}>
            SELECTED SERVICE
          </span>
          <div
            style={{
              backgroundColor: '#081224',
              border: '1px solid #1e3a6c',
              borderRadius: '6px',
              padding: '8px 14px',
              fontSize: '0.85rem',
              fontWeight: 700,
              color: '#f8fafc',
              minWidth: '240px'
            }}
          >
            {selectedTrain ? `${selectedTrain.train_number} — ${selectedTrain.train_name}` : '12926 — Paschim Superfast Express'}
          </div>
        </div>

        {/* Inject Additional Delay */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <span style={{ fontSize: '0.65rem', fontWeight: 800, color: '#64748b', letterSpacing: '0.5px' }}>
            INJECT ADDITIONAL DELAY (MINUTES)
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <input
              type="number"
              min="0"
              max="240"
              value={injectedDelay}
              onChange={(e) => setInjectedDelay(Number(e.target.value))}
              style={{
                backgroundColor: '#081224',
                border: '1px solid #1e3a6c',
                color: '#f8fafc',
                padding: '7px 12px',
                borderRadius: '6px',
                fontSize: '0.95rem',
                fontWeight: 800,
                width: '70px',
                textAlign: 'center',
                outline: 'none'
              }}
            />

            {[5, 10, 20, 30, 60].map((m) => (
              <button
                key={m}
                onClick={() => handleQuickAdd(m)}
                style={{
                  backgroundColor: injectedDelay === m ? '#0284c7' : '#081224',
                  border: '1px solid #1e3a6c',
                  color: injectedDelay === m ? '#ffffff' : '#94a3b8',
                  padding: '7px 12px',
                  borderRadius: '6px',
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  cursor: 'pointer'
                }}
              >
                +{m}m
              </button>
            ))}
          </div>
        </div>

        {/* Run Simulation Button */}
        <div style={{ alignSelf: 'flex-end' }}>
          <button
            onClick={() => executeSimulation()}
            disabled={loading}
            style={{
              backgroundColor: '#0284c7',
              border: 'none',
              color: 'white',
              padding: '10px 20px',
              borderRadius: '6px',
              fontSize: '0.85rem',
              fontWeight: 800,
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 0 14px rgba(2, 132, 199, 0.4)',
              letterSpacing: '0.5px'
            }}
          >
            {loading ? <RefreshCw size={15} className="spin" /> : <Zap size={15} />}
            <span>RUN SIMULATION</span>
          </button>
        </div>
      </div>

      {/* Scenario Comparison Matrix (Image 1) */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#64748b', letterSpacing: '0.5px' }}>
          SCENARIO COMPARISON MATRIX
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1.15fr', gap: '16px', alignItems: 'center' }}>
          {/* Baseline Situation Card */}
          <div
            style={{
              backgroundColor: '#0c1a33',
              border: '1px solid #1e3a6c',
              borderRadius: '10px',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px'
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#94a3b8', letterSpacing: '0.5px' }}>
              BASELINE SITUATION
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Proactive ETA:</span>
              <span style={{ fontSize: '1.2rem', fontWeight: 800, color: '#f8fafc' }}>
                {simulationResult?.baseline_eta.split(' ')[0] || '15:07'}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Expected Delay:</span>
              <span style={{ fontSize: '1rem', fontWeight: 800, color: '#38bdf8' }}>
                +{simulationResult?.baseline_delay_minutes?.toFixed(0) || '22'} min
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Corridor Risk:</span>
              <span
                style={{
                  backgroundColor: 'rgba(16, 185, 129, 0.15)',
                  color: '#10b981',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  fontSize: '0.72rem',
                  fontWeight: 800
                }}
              >
                {simulationResult?.corridor_risk || 'LOW'}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Downstream Impacted:</span>
              <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc' }}>
                {simulationResult?.affected_cascading_trains_count || 3} services
              </span>
            </div>
          </div>

          {/* Central Transition Arrow */}
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <div
              style={{
                backgroundColor: '#0c1a33',
                border: '1px solid #1e3a6c',
                width: '38px',
                height: '38px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#38bdf8'
              }}
            >
              <ArrowRight size={18} />
            </div>
          </div>

          {/* Simulated Scenario (+N min Delay) Card (Cyan Highlight) */}
          <div
            style={{
              backgroundColor: 'rgba(2, 132, 199, 0.06)',
              border: '1.5px solid #0284c7',
              borderRadius: '10px',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px',
              boxShadow: '0 0 16px rgba(2, 132, 199, 0.25)'
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#38bdf8', letterSpacing: '0.5px' }}>
              SIMULATED SCENARIO (+{injectedDelay} MIN DELAY)
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>New Proactive ETA:</span>
              <span style={{ fontSize: '1.35rem', fontWeight: 800, color: '#38bdf8' }}>
                {simulationResult?.intervention_eta.split(' ')[0] || '15:20'}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>New Total Delay:</span>
              <span style={{ fontSize: '1rem', fontWeight: 800, color: '#fbbf24' }}>
                +{simulationResult?.intervention_delay_minutes?.toFixed(0) || '35'} min
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Escalated Risk:</span>
              <span
                style={{
                  backgroundColor: 'rgba(245, 158, 11, 0.15)',
                  color: '#fbbf24',
                  border: '1px solid rgba(245, 158, 11, 0.3)',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  fontSize: '0.72rem',
                  fontWeight: 800
                }}
              >
                {simulationResult?.escalated_risk || 'MEDIUM'}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Total Cascaded Impact:</span>
              <span style={{ fontSize: '0.95rem', fontWeight: 800, color: '#f87171' }}>
                +{simulationResult?.total_cascaded_impact_min?.toFixed(1) || '13.5'} min (+{simulationResult?.net_cascaded_escalation_min?.toFixed(1) || '5.5'} min net)
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Downstream Train Absorption Delta Table (Image 1) */}
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
          DOWNSTREAM TRAIN ABSORPTION DELTA
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #1e3a6c', color: '#64748b', textAlign: 'left' }}>
                <th style={{ padding: '8px 12px' }}>TRAIN</th>
                <th style={{ padding: '8px 12px' }}>BASELINE INDUCED DELAY</th>
                <th style={{ padding: '8px 12px' }}>SIMULATED INDUCED DELAY</th>
                <th style={{ padding: '8px 12px' }}>NET ESCALATION</th>
              </tr>
            </thead>
            <tbody>
              {simulationResult?.downstream_absorption && simulationResult.downstream_absorption.length > 0 ? (
                simulationResult.downstream_absorption.map((row: any, idx: number) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #14284b' }}>
                    <td style={{ padding: '10px 12px', fontWeight: 700, color: '#f8fafc' }}>
                      {row.train_number} — {row.train_name}
                    </td>
                    <td style={{ padding: '10px 12px', color: '#94a3b8' }}>
                      {row.baseline_induced_delay}
                    </td>
                    <td style={{ padding: '10px 12px', color: '#fbbf24', fontWeight: 700 }}>
                      {row.simulated_induced_delay}
                    </td>
                    <td style={{ padding: '10px 12px', color: '#f87171', fontWeight: 800 }}>
                      {row.net_escalation}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} style={{ padding: '20px', textAlign: 'center', color: '#64748b' }}>
                    No trailing trains exposed to bottleneck clearance buffer.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
