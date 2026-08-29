import React, { useEffect, useState } from 'react';
import { WhereIsMyTrainView } from './components/WhereIsMyTrainView';
import { MLStudioView } from './components/MLStudioView';
import { HistoricalDataDashboard } from './components/HistoricalDataDashboard';

import { SimulationWebSocket } from './services/websocket';
import {
  fetchNetworkState,
  fetchTrains,
  fetchCOAEvents,
  startSimulation,
  pauseSimulation,
  resetSimulation,
  setSimulationSpeed
} from './services/api';
import { SimulationState, TrainState, COAEvent } from './types';
import { Train, Cpu, ShieldAlert, Database } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'PASSENGER' | 'ML_STUDIO' | 'HISTORICAL_DATA'>('PASSENGER');
  
  const [simulationState, setSimulationState] = useState<SimulationState | null>(null);
  const [networkState, setNetworkState] = useState<{ stations: any[]; sections: any[] } | null>(null);
  const [trains, setTrains] = useState<TrainState[]>([]);
  const [selectedTrainId, setSelectedTrainId] = useState<string>('TRAIN_12951');
  const [selectedTrain, setSelectedTrain] = useState<TrainState | null>(null);
  const [coaLogs, setCoaLogs] = useState<COAEvent[]>([]);

  // Modals
  const [isIncidentModalOpen, setIsIncidentModalOpen] = useState<boolean>(false);
  const [isMetricsModalOpen, setIsMetricsModalOpen] = useState<boolean>(false);

  useEffect(() => {
    // Fetch initial trains & network state once on mount
    fetchTrains().then((data) => {
      setTrains(data);
      if (data.length > 0 && !selectedTrainId) {
        setSelectedTrainId(data[0].train_id);
        setSelectedTrain(data[0]);
      }
    }).catch(console.error);

    fetchNetworkState().then(setNetworkState).catch(console.error);

    // COA event logs poll
    const interval = setInterval(() => {
      fetchCOAEvents().then(setCoaLogs).catch(() => {});
    }, 2000);

    return () => {
      clearInterval(interval);
    };
  }, []);

  // WebSocket connection for live telemetry & dynamic ETA engine
  useEffect(() => {
    const ws = new SimulationWebSocket((newState) => {
      setSimulationState(newState);
      setTrains(newState.trains);
    });
    ws.connect();

    return () => {
      ws.disconnect();
    };
  }, []);

  // Keep selectedTrain synced when selectedTrainId or trains list changes
  useEffect(() => {
    const found = trains.find((t) => t.train_id === selectedTrainId);
    if (found) {
      setSelectedTrain(found);
    }
  }, [selectedTrainId, trains]);

  const handleStart = async () => { await startSimulation(); };
  const handlePause = async () => { await pauseSimulation(); };
  const handleReset = async () => { await resetSimulation(); setSelectedTrain(null); };
  const handleSetSpeed = async (multiplier: number) => { await setSimulationSpeed(multiplier); };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#070b14' }}>
      
      {/* Top Application Bar with Mode Switcher */}
      <header className="glass-panel" style={{
        borderRadius: 0,
        borderTop: 0,
        borderLeft: 0,
        borderRight: 0,
        padding: '10px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        zIndex: 1000
      }}>
        
        {/* Brand Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #0284c7 0%, #3b82f6 100%)',
            padding: '8px',
            borderRadius: '8px',
            boxShadow: '0 0 12px rgba(56, 189, 248, 0.4)'
          }}>
            <Train size={20} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.15rem', fontWeight: 700, letterSpacing: '-0.5px' }}>
                SIH26028 Dynamic Train ETA System
              </h1>
              <span style={{
                background: 'rgba(56, 189, 248, 0.15)',
                color: '#38bdf8',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                padding: '2px 6px',
                borderRadius: '4px',
                fontSize: '0.65rem',
                fontWeight: 700
              }}>
                MINISTRY OF RAILWAYS
              </span>
            </div>
            <p style={{ fontSize: '0.7rem', color: '#94a3b8' }}>
              Live Operations & Learning-Based Forecast Engine
            </p>
          </div>
        </div>

        {/* View Mode Navigation Switcher */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          background: 'rgba(15, 23, 42, 0.8)',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          padding: '4px',
          borderRadius: '24px',
          gap: '4px'
        }}>
          <button
            onClick={() => setActiveTab('PASSENGER')}
            style={{
              background: activeTab === 'PASSENGER' ? 'linear-gradient(135deg, #0284c7 0%, #2563eb 100%)' : 'transparent',
              color: activeTab === 'PASSENGER' ? '#ffffff' : '#94a3b8',
              border: 'none',
              padding: '6px 16px',
              borderRadius: '20px',
              fontSize: '0.78rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s ease-in-out',
              boxShadow: activeTab === 'PASSENGER' ? '0 2px 10px rgba(37, 99, 235, 0.4)' : 'none'
            }}
          >
            <span>🚆</span>
            <span>Passenger View ("Where is My Train")</span>
          </button>

          <button
            onClick={() => setActiveTab('HISTORICAL_DATA')}
            style={{
              background: activeTab === 'HISTORICAL_DATA' ? 'linear-gradient(135deg, #0284c7 0%, #0891b2 100%)' : 'transparent',
              color: activeTab === 'HISTORICAL_DATA' ? '#ffffff' : '#94a3b8',
              border: 'none',
              padding: '6px 16px',
              borderRadius: '20px',
              fontSize: '0.78rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s ease-in-out',
              boxShadow: activeTab === 'HISTORICAL_DATA' ? '0 2px 10px rgba(8, 145, 178, 0.4)' : 'none'
            }}
          >
            <Database size={14} />
            <span>Historical Data & ML Pipeline</span>
          </button>

          <button
            onClick={() => setActiveTab('ML_STUDIO')}
            style={{
              background: activeTab === 'ML_STUDIO' ? 'linear-gradient(135deg, #7c3aed 0%, #a855f7 100%)' : 'transparent',
              color: activeTab === 'ML_STUDIO' ? '#ffffff' : '#94a3b8',
              border: 'none',
              padding: '6px 16px',
              borderRadius: '20px',
              fontSize: '0.78rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s ease-in-out',
              boxShadow: activeTab === 'ML_STUDIO' ? '0 2px 10px rgba(168, 85, 247, 0.4)' : 'none'
            }}
          >
            <Cpu size={14} />
            <span>ML & Ops Control Studio</span>
          </button>
        </div>

        {/* Status Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.75rem', color: '#fbbf24' }}>
          <ShieldAlert size={14} />
          <span>Backend Learning Engine Active</span>
        </div>

      </header>

      {/* Main View Area */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        {activeTab === 'PASSENGER' ? (
          <WhereIsMyTrainView
            trains={trains}
            selectedTrainId={selectedTrainId}
            onSelectTrain={(tId) => {
              setSelectedTrainId(tId);
              const found = trains.find((t) => t.train_id === tId);
              if (found) setSelectedTrain(found);
            }}
          />
        ) : activeTab === 'HISTORICAL_DATA' ? (
          <HistoricalDataDashboard />
        ) : (
          <MLStudioView
            simulationState={simulationState}
            networkState={networkState}
            selectedTrain={selectedTrain}
            onSelectTrain={setSelectedTrain}
            coaLogs={coaLogs}
            onStart={handleStart}
            onPause={handlePause}
            onReset={handleReset}
            onSetSpeed={handleSetSpeed}
            isIncidentModalOpen={isIncidentModalOpen}
            setIsIncidentModalOpen={setIsIncidentModalOpen}
            isMetricsModalOpen={isMetricsModalOpen}
            setIsMetricsModalOpen={setIsMetricsModalOpen}
          />
        )}
      </div>

    </div>
  );
};
;

export default App;
