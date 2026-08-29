import React, { useState } from 'react';
import { ControlPanel } from './ControlPanel';
import { DemoScenarioBar } from './DemoScenarioBar';
import { RailwayMap } from '../map/RailwayMap';
import { TrainDrawer } from './TrainDrawer';
import { IncidentModal } from './IncidentModal';
import { ModelMetricsModal } from './ModelMetricsModal';
import { CounterfactualLabModal } from './CounterfactualLabModal';

import { SimulationState, TrainState, COAEvent } from '../types';
import { Terminal, Cpu, AlertTriangle, Sliders } from 'lucide-react';

interface MLStudioViewProps {
  simulationState: SimulationState | null;
  networkState: { stations: any[]; sections: any[] } | null;
  selectedTrain: TrainState | null;
  onSelectTrain: (train: TrainState | null) => void;
  coaLogs: COAEvent[];
  onStart: () => void;
  onPause: () => void;
  onReset: () => void;
  onSetSpeed: (speed: number) => void;
  isIncidentModalOpen: boolean;
  setIsIncidentModalOpen: (open: boolean) => void;
  isMetricsModalOpen: boolean;
  setIsMetricsModalOpen: (open: boolean) => void;
}

export const MLStudioView: React.FC<MLStudioViewProps> = ({
  simulationState,
  networkState,
  selectedTrain,
  onSelectTrain,
  coaLogs,
  onStart,
  onPause,
  onReset,
  onSetSpeed,
  isIncidentModalOpen,
  setIsIncidentModalOpen,
  isMetricsModalOpen,
  setIsMetricsModalOpen
}) => {
  const [isCounterfactualModalOpen, setIsCounterfactualModalOpen] = useState<boolean>(false);

  return (
    <div style={{ flex: 1, display: 'flex', position: 'relative', overflow: 'hidden', height: '100%' }}>
      
      {/* Left Interactive Map Container */}
      <div style={{ flex: 1, position: 'relative' }}>
        <RailwayMap
          simulationState={simulationState}
          networkState={networkState}
          onSelectTrain={onSelectTrain}
          selectedTrainId={selectedTrain?.train_id}
        />

        {/* Floating Controls & Scenario Bar */}
        <div style={{
          position: 'absolute',
          top: '16px',
          left: '16px',
          right: selectedTrain ? '470px' : '16px',
          zIndex: 800,
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          pointerEvents: 'none'
        }}>
          <div style={{ pointerEvents: 'auto' }}>
            <ControlPanel
              simulationState={simulationState}
              onStart={onStart}
              onPause={onPause}
              onReset={onReset}
              onSetSpeed={onSetSpeed}
            />
          </div>

          <div style={{ pointerEvents: 'auto' }}>
            <DemoScenarioBar />
          </div>
        </div>

        {/* Floating Admin Quick Actions */}
        <div style={{
          position: 'absolute',
          top: '16px',
          right: selectedTrain ? '470px' : '16px',
          zIndex: 850,
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          transition: 'right 0.3s ease-in-out'
        }}>
          <button className="glass-button" onClick={() => setIsCounterfactualModalOpen(true)}>
            <Sliders size={16} color="#38bdf8" />
            <span>Counterfactual Lab</span>
          </button>

          <button className="glass-button" onClick={() => setIsMetricsModalOpen(true)}>
            <Cpu size={16} color="#a855f7" />
            <span>ML Retrain & Performance Studio</span>
          </button>
          
          <button className="glass-button glass-button-danger" onClick={() => setIsIncidentModalOpen(true)}>
            <AlertTriangle size={16} />
            <span>Inject Incident</span>
          </button>
        </div>

        {/* Bottom Floating COA Event Stream */}
        <div className="glass-panel" style={{
          position: 'absolute',
          bottom: '16px',
          left: '16px',
          width: '420px',
          maxHeight: '160px',
          zIndex: 800,
          padding: '10px 14px',
          overflowY: 'auto'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px', fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8' }}>
            <Terminal size={14} />
            <span>LIVE COA OPERATIONAL LOG STREAM</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.72rem', fontFamily: 'monospace' }}>
            {coaLogs.length === 0 ? (
              <div style={{ color: '#64748b' }}>Awaiting operational events...</div>
            ) : (
              coaLogs.slice(0, 5).map((evt) => (
                <div key={evt.event_id} style={{ color: evt.severity === 'HIGH' || evt.severity === 'CRITICAL' ? '#f87171' : '#cbd5e1' }}>
                  [{evt.timestamp}] <strong>{evt.event_type}</strong>: {evt.description}
                </div>
              ))
            )}
          </div>
        </div>

      </div>

      {/* Right Train Details Inspector Drawer */}
      <TrainDrawer
        train={selectedTrain}
        onClose={() => onSelectTrain(null)}
      />

      {/* Incident Injection Modal */}
      <IncidentModal
        isOpen={isIncidentModalOpen}
        onClose={() => setIsIncidentModalOpen(false)}
      />

      {/* ML Model Performance Metrics Modal */}
      <ModelMetricsModal
        isOpen={isMetricsModalOpen}
        onClose={() => setIsMetricsModalOpen(false)}
      />

      {/* Counterfactual What-If Lab Modal */}
      <CounterfactualLabModal
        isOpen={isCounterfactualModalOpen}
        onClose={() => setIsCounterfactualModalOpen(false)}
      />

    </div>
  );
};

export default MLStudioView;
