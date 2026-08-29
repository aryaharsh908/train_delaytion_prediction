import React, { useState } from 'react';
import { X, Play, Sliders, Layers, AlertCircle, TrendingDown, Users } from 'lucide-react';
import { CounterfactualRequest, CounterfactualResponse } from '../types';
import { runCounterfactualSimulation } from '../services/api';

interface CounterfactualLabModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CounterfactualLabModal: React.FC<CounterfactualLabModalProps> = ({ isOpen, onClose }) => {
  const [interventionType, setInterventionType] = useState<'PRIORITY_BOOST' | 'TSR_IMPOSITION' | 'WEATHER_SPEED_DROP'>('PRIORITY_BOOST');
  const [trainNumber, setTrainNumber] = useState<string>('12951');
  const [sectionId, setSectionId] = useState<string>('NDLS-MTJ');
  const [tsrSpeed, setTsrSpeed] = useState<number>(30);
  const [distanceKm, setDistanceKm] = useState<number>(50);
  
  const [loading, setLoading] = useState<boolean>(false);
  const [simulationResult, setSimulationResult] = useState<CounterfactualResponse | null>(null);

  if (!isOpen) return null;

  const handleRunSimulation = async () => {
    setLoading(true);
    try {
      const req: CounterfactualRequest = {
        train_id: `TRAIN_${trainNumber}`,
        train_number: trainNumber,
        intervention_type: interventionType,
        section_id: sectionId,
        speed_restriction_kmh: tsrSpeed,
        distance_km: distanceKm
      };
      const res = await runCounterfactualSimulation(req);
      setSimulationResult(res);
    } catch (err) {
      console.error('Counterfactual simulation failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(2, 6, 23, 0.85)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 2000
    }}>
      <div className="glass-panel" style={{ width: '820px', maxHeight: '90vh', padding: '24px', borderRadius: '16px', overflowY: 'auto' }}>
        
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ background: 'linear-gradient(135deg, #7c3aed 0%, #a855f7 100%)', padding: '8px', borderRadius: '10px' }}>
              <Sliders size={20} color="white" />
            </div>
            <div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'white' }}>Counterfactual What-If Simulation Lab</h2>
              <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Dispatcher Intervention Modeling & Network Delay Impact Predictor</p>
            </div>
          </div>
          <button className="glass-button" onClick={onClose} style={{ padding: '6px', borderRadius: '50%' }}>
            <X size={18} />
          </button>
        </div>

        {/* Configuration Panel */}
        <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '12px', marginBottom: '20px', border: '1px solid rgba(255,255,255,0.08)' }}>
          <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#38bdf8', marginBottom: '12px' }}>
            1. Configure Operational Intervention
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '14px' }}>
            
            {/* Intervention Selector */}
            <div>
              <label style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Intervention Type</label>
              <select
                value={interventionType}
                onChange={(e: any) => setInterventionType(e.target.value)}
                style={{ width: '100%', background: '#0f172a', border: '1px solid rgba(56, 189, 248, 0.4)', color: 'white', padding: '8px', borderRadius: '8px', fontSize: '0.8rem' }}
              >
                <option value="PRIORITY_BOOST">🚀 Priority Precedence Upgrade</option>
                <option value="TSR_IMPOSITION">⚠️ Temporary Speed Restriction (TSR)</option>
                <option value="WEATHER_SPEED_DROP">🌫️ Fog/Weather Speed Penalty</option>
              </select>
            </div>

            {/* Target Train */}
            <div>
              <label style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Target Train</label>
              <select
                value={trainNumber}
                onChange={(e) => setTrainNumber(e.target.value)}
                style={{ width: '100%', background: '#0f172a', border: '1px solid rgba(56, 189, 248, 0.4)', color: 'white', padding: '8px', borderRadius: '8px', fontSize: '0.8rem' }}
              >
                <option value="12951">12951 Mumbai Rajdhani</option>
                <option value="12302">12302 Howrah Rajdhani</option>
                <option value="12626">12626 Kerala Express</option>
                <option value="12002">12002 Shatabdi Express</option>
              </select>
            </div>

            {/* Target Section */}
            <div>
              <label style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Target Section</label>
              <input
                type="text"
                value={sectionId}
                onChange={(e) => setSectionId(e.target.value)}
                style={{ width: '100%', background: '#0f172a', border: '1px solid rgba(56, 189, 248, 0.4)', color: 'white', padding: '8px', borderRadius: '8px', fontSize: '0.8rem' }}
              />
            </div>

          </div>

          {/* Conditional Controls */}
          {interventionType === 'TSR_IMPOSITION' && (
            <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: '0.72rem', color: '#94a3b8' }}>TSR Speed Limit: {tsrSpeed} km/h</label>
                <input type="range" min="15" max="60" value={tsrSpeed} onChange={(e) => setTsrSpeed(Number(e.target.value))} style={{ width: '100%' }} />
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Affected Length: {distanceKm} km</label>
                <input type="range" min="10" max="150" value={distanceKm} onChange={(e) => setDistanceKm(Number(e.target.value))} style={{ width: '100%' }} />
              </div>
            </div>
          )}

          <div style={{ marginTop: '14px', display: 'flex', justifyContent: 'flex-end' }}>
            <button
              className="glass-button glass-button-primary"
              onClick={handleRunSimulation}
              disabled={loading}
              style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 20px', borderRadius: '20px' }}
            >
              <Play size={16} />
              <span>{loading ? 'Simulating Intervention...' : 'Run Counterfactual What-If Engine'}</span>
            </button>
          </div>
        </div>

        {/* Results View */}
        {simulationResult && (
          <div>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#a855f7', marginBottom: '10px' }}>
              2. Structural Simulation Impact & Network Metrics
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '10px', marginBottom: '16px' }}>
              <div style={{ background: 'rgba(30, 41, 59, 0.7)', padding: '12px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
                <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Baseline ETA</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#f8fafc' }}>{simulationResult.baseline_eta}</div>
              </div>

              <div style={{ background: 'rgba(30, 41, 59, 0.7)', padding: '12px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
                <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Intervention ETA</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 800, color: simulationResult.delay_change_minutes <= 0 ? '#34d399' : '#ef4444' }}>
                  {simulationResult.intervention_eta}
                </div>
              </div>

              <div style={{ background: 'rgba(30, 41, 59, 0.7)', padding: '12px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
                <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Net Passenger-Minutes</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 800, color: simulationResult.network_passenger_minutes_added <= 0 ? '#34d399' : '#ef4444' }}>
                  {simulationResult.network_passenger_minutes_added > 0 ? `+${simulationResult.network_passenger_minutes_added}` : simulationResult.network_passenger_minutes_added} m
                </div>
              </div>

              <div style={{ background: 'rgba(30, 41, 59, 0.7)', padding: '12px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
                <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Cascading Trains</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#38bdf8' }}>{simulationResult.affected_cascading_trains_count} Trains</div>
              </div>
            </div>

            {/* Fan-Chart Quantiles Card */}
            <div style={{ background: 'rgba(56, 189, 248, 0.1)', padding: '14px', borderRadius: '10px', border: '1px solid rgba(56, 189, 248, 0.3)', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#38bdf8' }}>
                  📊 Probabilistic Quantile Uncertainty Range under Intervention
                </span>
                <span style={{ fontSize: '0.72rem', color: '#34d399', fontWeight: 700 }}>
                  Confidence Score: {simulationResult.confidence_score}%
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '20px', fontSize: '0.85rem' }}>
                <div>P10 (Best Case): <strong style={{ color: '#6ee7b7' }}>{simulationResult.eta_p10}</strong></div>
                <div>P50 (Median): <strong style={{ color: '#38bdf8' }}>{simulationResult.eta_p50}</strong></div>
                <div>P90 (Worst Case): <strong style={{ color: '#fca5a5' }}>{simulationResult.eta_p90}</strong></div>
              </div>
            </div>

          </div>
        )}

      </div>
    </div>
  );
};
