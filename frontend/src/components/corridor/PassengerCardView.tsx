import React from 'react';
import { Clock, MapPin, AlertCircle, Info, CheckCircle2, Train } from 'lucide-react';
import { TrainState, TrainETAComparison } from '../../types';
import { WhereIsMyTrainView } from '../WhereIsMyTrainView';

interface PassengerCardViewProps {
  trains: TrainState[];
  selectedTrainId: string;
  selectedTrain: TrainState | null;
  selectedTrainETA: TrainETAComparison | null;
  onSelectTrain: (trainId: string) => void;
}

export const PassengerCardView: React.FC<PassengerCardViewProps> = ({
  trains,
  selectedTrainId,
  selectedTrain,
  selectedTrainETA,
  onSelectTrain
}) => {
  const statusMsg = selectedTrainETA?.status_message || selectedTrain?.last_event_description || 'Running on time';
  const delay = selectedTrain?.current_delay_minutes || 0;
  const isDelayed = delay >= 5;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflowY: 'auto' }}>
      {/* Simplified Passenger Card (Grounded in authentic delay_reasons and status_message) */}
      <div
        style={{
          margin: '20px 24px 0 24px',
          backgroundColor: '#0c1a33',
          border: `1.5px solid ${isDelayed ? '#f59e0b' : '#0284c7'}`,
          borderRadius: '12px',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
          boxShadow: isDelayed ? '0 0 16px rgba(245, 158, 11, 0.15)' : '0 0 16px rgba(2, 132, 199, 0.15)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                backgroundColor: isDelayed ? '#f59e0b' : '#0284c7',
                padding: '10px',
                borderRadius: '8px',
                color: '#ffffff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Train size={20} />
            </div>
            <div>
              <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#f8fafc' }}>
                {selectedTrain ? `${selectedTrain.train_number} — ${selectedTrain.train_name}` : '12926 — Paschim Superfast Express'}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                {selectedTrain?.origin_station_name || 'Origin'} ➔ {selectedTrain?.destination_station_name || 'Destination'}
              </div>
            </div>
          </div>

          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 700 }}>
              ESTIMATED ARRIVAL (PROACTIVE)
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: isDelayed ? '#fbbf24' : '#10b981' }}>
              {selectedTrainETA?.proactive_forecast_eta?.split(' ')[0] || '--:--'}
            </div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
              Scheduled: {selectedTrainETA?.scheduled_timetable_eta || '--:--'}
            </div>
          </div>
        </div>

        {/* Live Operational Status Banner (Authentic status_message) */}
        <div
          style={{
            backgroundColor: isDelayed ? 'rgba(245, 158, 11, 0.1)' : 'rgba(16, 185, 129, 0.1)',
            border: `1px solid ${isDelayed ? 'rgba(245, 158, 11, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
            padding: '10px 14px',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}
        >
          {isDelayed ? <AlertCircle size={16} color="#fbbf24" /> : <CheckCircle2 size={16} color="#10b981" />}
          <div style={{ fontSize: '0.82rem', fontWeight: 700, color: isDelayed ? '#fbbf24' : '#10b981' }}>
            {statusMsg}
          </div>
        </div>

        {/* Explainability Breakdown grounded in real delay_reasons */}
        {selectedTrain?.current_eta?.explainability_factors && selectedTrain.current_eta.explainability_factors.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div style={{ fontSize: '0.7rem', fontWeight: 800, color: '#64748b', letterSpacing: '0.5px' }}>
              OPERATIONAL DELAY FACTORS:
            </div>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {selectedTrain.current_eta.explainability_factors.map((f, idx) => (
                <div
                  key={idx}
                  style={{
                    backgroundColor: '#081224',
                    border: '1px solid #1e3a6c',
                    padding: '6px 10px',
                    borderRadius: '6px',
                    fontSize: '0.72rem',
                    color: '#e2e8f0',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <span style={{ color: '#fbbf24', fontWeight: 700 }}>+{f.impact_minutes.toFixed(0)}m</span>
                  <span>{f.factor_name}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Embedded WhereIsMyTrain Station Timeline */}
      <div style={{ flex: 1, minHeight: '500px' }}>
        <WhereIsMyTrainView
          trains={trains}
          selectedTrainId={selectedTrainId}
          onSelectTrain={onSelectTrain}
        />
      </div>
    </div>
  );
};
