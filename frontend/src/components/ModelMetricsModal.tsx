import React, { useEffect, useState } from 'react';
import { X, Cpu, CheckCircle, BarChart3, TrendingUp } from 'lucide-react';
import { fetchModelMetrics, triggerModelRetrain } from '../services/api';
import { ModelMetrics } from '../types';

interface ModelMetricsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ModelMetricsModal: React.FC<ModelMetricsModalProps> = ({ isOpen, onClose }) => {
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isRetraining, setIsRetraining] = useState<boolean>(false);

  const handleRetrain = () => {
    setIsRetraining(true);
    triggerModelRetrain()
      .then((res) => {
        setMetrics(res.metrics);
        setIsRetraining(false);
      })
      .catch((err) => {
        console.error('Error retraining model:', err);
        setIsRetraining(false);
      });
  };

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      fetchModelMetrics()
        .then((data) => {
          setMetrics(data);
          setLoading(false);
        })
        .catch((err) => {
          console.error('Error fetching metrics:', err);
          setLoading(false);
        });
    }
  }, [isOpen]);

  if (!isOpen) return null;

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
      zIndex: 9999
    }}>
      <div className="glass-panel" style={{ width: '680px', maxHeight: '85vh', overflowY: 'auto', padding: '24px' }}>
        
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Cpu color="#a855f7" size={24} />
            <div>
              <h2 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.2rem', fontWeight: 700 }}>
                Machine Learning Baseline Model Evaluation
              </h2>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                Trained on 15,000+ Multi-Corridor Historical Runs across Indian Railways Corridors
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              className="glass-button glass-button-primary"
              onClick={handleRetrain}
              disabled={isRetraining}
              style={{ fontSize: '0.75rem', padding: '6px 12px' }}
            >
              {isRetraining ? 'Retraining...' : '🚀 Retrain Model'}
            </button>
            <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
              <X size={20} />
            </button>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>
            Loading baseline metrics...
          </div>
        ) : metrics ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            
            {/* Comparison Cards Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              
              {/* ML Model Card */}
              <div className="glass-panel-glow" style={{ padding: '16px', borderRadius: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.85rem', color: '#38bdf8' }}>
                    PROPOSED ML ETA MODEL
                  </span>
                  {metrics.naive_mae && metrics.ml_mae && metrics.naive_mae > 0 ? (
                    <span style={{ fontSize: '0.7rem', color: '#34d399', background: 'rgba(16,185,129,0.15)', padding: '2px 6px', borderRadius: '4px' }}>
                      +{Math.round((1 - metrics.ml_mae / metrics.naive_mae) * 100)}% IMPROVEMENT
                    </span>
                  ) : null}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.8rem' }}>
                  <div>
                    <span style={{ color: '#64748b', display: 'block', fontSize: '0.7rem' }}>MEAN ABS ERROR (MAE)</span>
                    <strong style={{ fontSize: '1.2rem', color: '#f8fafc' }}>{metrics.ml_mae ?? '—'} <span style={{ fontSize: '0.75rem' }}>min</span></strong>
                  </div>
                  <div>
                    <span style={{ color: '#64748b', display: 'block', fontSize: '0.7rem' }}>ROOT MEAN SQ ERROR (RMSE)</span>
                    <strong style={{ fontSize: '1.2rem', color: '#f8fafc' }}>{metrics.ml_rmse ?? '—'} <span style={{ fontSize: '0.75rem' }}>min</span></strong>
                  </div>
                  <div>
                    <span style={{ color: '#64748b', display: 'block', fontSize: '0.7rem' }}>PREDICTIONS WITHIN 5 MIN</span>
                    <strong style={{ color: '#34d399' }}>{metrics.ml_within_5min_pct != null ? `${metrics.ml_within_5min_pct}%` : '—'}</strong>
                  </div>
                  <div>
                    <span style={{ color: '#64748b', display: 'block', fontSize: '0.7rem' }}>PREDICTIONS WITHIN 10 MIN</span>
                    <strong style={{ color: '#34d399' }}>{metrics.ml_within_10min_pct != null ? `${metrics.ml_within_10min_pct}%` : '—'}</strong>
                  </div>
                </div>
              </div>

              {/* Naive Baseline Card */}
              <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.85rem', color: '#64748b' }}>
                    NAIVE TIMETABLE BASELINE
                  </span>
                  <span style={{ fontSize: '0.7rem', color: '#64748b' }}>Static Timetable</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.8rem' }}>
                  <div>
                    <span style={{ color: '#64748b', display: 'block', fontSize: '0.7rem' }}>MEAN ABS ERROR (MAE)</span>
                    <strong style={{ fontSize: '1.2rem', color: '#94a3b8' }}>{metrics.naive_mae ?? '—'} <span style={{ fontSize: '0.75rem' }}>min</span></strong>
                  </div>
                  <div>
                    <span style={{ color: '#64748b', display: 'block', fontSize: '0.7rem' }}>ROOT MEAN SQ ERROR (RMSE)</span>
                    <strong style={{ fontSize: '1.2rem', color: '#94a3b8' }}>{metrics.naive_rmse ?? '—'} <span style={{ fontSize: '0.75rem' }}>min</span></strong>
                  </div>
                  <div>
                    <span style={{ color: '#64748b', display: 'block', fontSize: '0.7rem' }}>PREDICTIONS WITHIN 5 MIN</span>
                    <strong style={{ color: '#fbbf24' }}>{metrics.naive_within_5min_pct != null ? `${metrics.naive_within_5min_pct}%` : '—'}</strong>
                  </div>
                  <div>
                    <span style={{ color: '#64748b', display: 'block', fontSize: '0.7rem' }}>PREDICTIONS WITHIN 10 MIN</span>
                    <strong style={{ color: '#fbbf24' }}>{metrics.naive_within_10min_pct != null ? `${metrics.naive_within_10min_pct}%` : '—'}</strong>
                  </div>
                </div>
              </div>

            </div>

            {/* Feature Importance Table */}
            <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '14px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <BarChart3 size={16} color="#a855f7" />
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f8fafc' }}>
                  Feature Importance Weights
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {Object.entries(metrics.feature_importances).map(([feat, weight]) => (
                  <div key={feat} style={{ fontSize: '0.75rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px', color: '#cbd5e1' }}>
                      <span>{feat}</span>
                      <span>{(weight * 100).toFixed(1)}%</span>
                    </div>
                    <div style={{ height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${weight * 100}%`, background: 'linear-gradient(90deg, #a855f7, #38bdf8)', borderRadius: '3px' }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        ) : null}

      </div>
    </div>
  );
};
