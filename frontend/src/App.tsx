import React, { useEffect, useState } from 'react';
import { CorridorHeader } from './components/corridor/CorridorHeader';
import { CorridorSummaryBar } from './components/corridor/CorridorSummaryBar';
import { CorridorSidebar, CorridorNavTab } from './components/corridor/CorridorSidebar';
import { ForecastView } from './components/corridor/ForecastView';
import { DelayPropagationView } from './components/corridor/DelayPropagationView';
import { JunctionRiskView } from './components/corridor/JunctionRiskView';
import { WhatIfLabView } from './components/corridor/WhatIfLabView';
import { OperatorView } from './components/corridor/OperatorView';
import { PassengerCardView } from './components/corridor/PassengerCardView';
import { SwitchTrainModal } from './components/corridor/SwitchTrainModal';
import { DispatcherCopilot } from './components/corridor/DispatcherCopilot';
import { ChatConsole } from './components/corridor/ChatConsole';
import { AdvisoryPanel } from './components/corridor/AdvisoryPanel';

import { MLStudioView } from './components/MLStudioView';
import { HistoricalDataDashboard } from './components/HistoricalDataDashboard';
import { RailwayMap } from './map/RailwayMap';

import { SimulationWebSocket } from './services/websocket';
import {
  fetchTrains,
  fetchNetworkState,
  fetchCOAEvents,
  fetchCorridorHealth,
  fetchTrainETAComparison,
  fetchRankedJunctionConflicts,
  fetchDownstreamPropagation,
  syncCorridorTrain,
  startSimulation,
  pauseSimulation,
  resetSimulation,
  setSimulationSpeed
} from './services/api';

import {
  TrainState,
  SimulationState,
  COAEvent,
  TrainETAComparison,
  RankedJunctionConflict,
  DownstreamPropagationResponse,
  CorridorHealthSummary
} from './types';

export const App: React.FC = () => {
  const [activeNavTab, setActiveNavTab] = useState<CorridorNavTab>('WHAT_IF');

  // Corridor State
  const [trains, setTrains] = useState<TrainState[]>([]);
  const [selectedTrainId, setSelectedTrainId] = useState<string>('12926');
  const [selectedTrain, setSelectedTrain] = useState<TrainState | null>(null);
  const [corridorHealth, setCorridorHealth] = useState<CorridorHealthSummary | null>(null);

  // Deep Analytics State
  const [selectedTrainETA, setSelectedTrainETA] = useState<TrainETAComparison | null>(null);
  const [loadingETA, setLoadingETA] = useState<boolean>(false);
  const [conflicts, setConflicts] = useState<RankedJunctionConflict[]>([]);
  const [loadingConflicts, setLoadingConflicts] = useState<boolean>(false);
  const [propagationData, setPropagationData] = useState<DownstreamPropagationResponse | null>(null);
  const [loadingProp, setLoadingProp] = useState<boolean>(false);

  // Modals
  const [isSwitchModalOpen, setIsSwitchModalOpen] = useState<boolean>(false);
  const [isIncidentModalOpen, setIsIncidentModalOpen] = useState<boolean>(false);
  const [isMetricsModalOpen, setIsMetricsModalOpen] = useState<boolean>(false);

  // Legacy studio state
  const [simulationState, setSimulationState] = useState<SimulationState | null>(null);
  const [networkState, setNetworkState] = useState<{ stations: any[]; sections: any[] } | null>(null);
  const [coaLogs, setCoaLogs] = useState<COAEvent[]>([]);

  // 1. Initial hydration on mount
  useEffect(() => {
    fetchTrains()
      .then((data) => {
        setTrains(data);
        if (data.length > 0) {
          const defaultTrain = data.find((t) => t.train_number === '12926') || data[0];
          setSelectedTrainId(defaultTrain.train_number);
          setSelectedTrain(defaultTrain);
        }
      })
      .catch(console.error);

    fetchCorridorHealth().then(setCorridorHealth).catch(console.error);
    fetchNetworkState().then(setNetworkState).catch(console.error);

    // Initial junction conflicts
    setLoadingConflicts(true);
    fetchRankedJunctionConflicts()
      .then((res) => {
        setConflicts(res);
        setLoadingConflicts(false);
      })
      .catch(() => setLoadingConflicts(false));

    // COA poll
    const coaInterval = setInterval(() => {
      fetchCOAEvents().then(setCoaLogs).catch(() => {});
    }, 3000);

    return () => clearInterval(coaInterval);
  }, []);

  // 2. Fetch train ETA comparison & propagation whenever selectedTrainId changes
  useEffect(() => {
    if (!selectedTrainId) return;

    const cleanNum = selectedTrainId.replace(/^TRAIN_/i, '').trim();

    setLoadingETA(true);
    fetchTrainETAComparison(cleanNum)
      .then((data) => {
        setSelectedTrainETA(data);
        setLoadingETA(false);
      })
      .catch((err) => {
        console.error('Failed to fetch ETA comparison:', err);
        setLoadingETA(false);
      });

    setLoadingProp(true);
    fetchDownstreamPropagation(undefined, cleanNum)
      .then((data) => {
        setPropagationData(data);
        setLoadingProp(false);
      })
      .catch((err) => {
        console.error('Failed to fetch propagation:', err);
        setLoadingProp(false);
      });
  }, [selectedTrainId]);

  // 3. Keep selectedTrain reference in sync with trains list
  useEffect(() => {
    const cleanNum = selectedTrainId.replace(/^TRAIN_/i, '').trim();
    const found = trains.find(
      (t) => t.train_number === cleanNum || t.train_id === selectedTrainId || t.train_id === `TRAIN_${cleanNum}`
    );
    if (found) {
      setSelectedTrain(found);
    }
  }, [selectedTrainId, trains]);

  // 4. WebSocket connection for live telemetry stream
  useEffect(() => {
    const ws = new SimulationWebSocket((newState) => {
      setSimulationState(newState);
      if (newState.trains && newState.trains.length > 0) {
        setTrains(newState.trains);
      }
    });
    ws.connect();
    return () => ws.disconnect();
  }, []);

  // Train selector handler
  const handleSelectTrain = (trainIdOrNum: string) => {
    const clean = trainIdOrNum.replace(/^TRAIN_/i, '').trim();
    setSelectedTrainId(clean);
  };

  // Sync train input handler
  const handleSyncTrainNumber = async (trainNumber: string): Promise<boolean> => {
    const cleanNum = trainNumber.replace(/^TRAIN_/i, '').trim();
    if (!cleanNum) return false;

    try {
      const res = await syncCorridorTrain(cleanNum);
      if (res && res.success) {
        // Refresh trains list and select this train
        const updatedTrains = await fetchTrains();
        setTrains(updatedTrains);
        setSelectedTrainId(cleanNum);

        // Refresh corridor health & conflicts
        fetchCorridorHealth().then(setCorridorHealth).catch(console.error);
        fetchRankedJunctionConflicts().then(setConflicts).catch(console.error);
        return true;
      }
      return false;
    } catch (e) {
      console.error('Error syncing train number:', e);
      return false;
    }
  };

  const handleReset = () => {
    setSelectedTrainId('12926');
    fetchCorridorHealth().then(setCorridorHealth).catch(console.error);
    fetchRankedJunctionConflicts().then(setConflicts).catch(console.error);
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        width: '100vw',
        backgroundColor: '#070b14',
        color: '#f8fafc',
        fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        overflow: 'hidden'
      }}
    >
      {/* 1. RailSutra Top Application Bar */}
      <CorridorHeader
        selectedTrain={selectedTrain}
        trains={trains}
        onSelectTrain={handleSelectTrain}
        onSyncTrainNumber={handleSyncTrainNumber}
        onReset={handleReset}
        onOpenSwitchModal={() => setIsSwitchModalOpen(true)}
      />

      {/* 2. Corridor Summary Bar (Delhi - Mumbai Western Trunk Corridor) */}
      <CorridorSummaryBar summary={corridorHealth} />

      {/* 3. Main Workspace Area: Sidebar + Active View */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left Sidebar Navigation */}
        <CorridorSidebar activeTab={activeNavTab} onSelectTab={setActiveNavTab} />

        {/* Dynamic Center View Panel */}
        <main style={{ flex: 1, overflowY: 'auto', backgroundColor: '#070e1c', position: 'relative' }}>
          {activeNavTab === 'DISPATCHER_COPILOT' || activeNavTab === 'AI_EXPLAINER' ? (
            <DispatcherCopilot
              trains={trains}
              selectedTrainId={selectedTrainId}
              conflicts={conflicts}
              onSelectTrain={handleSelectTrain}
            />
          ) : activeNavTab === 'CHAT_CONSOLE' ? (
            <ChatConsole />
          ) : activeNavTab === 'ADVISORY_PANEL' ? (
            <AdvisoryPanel
              trains={trains}
              selectedTrainId={selectedTrainId}
              onSelectTrain={handleSelectTrain}
            />
          ) : activeNavTab === 'WHAT_IF' ? (
            <WhatIfLabView
              selectedTrain={selectedTrain}
              trains={trains}
              onSelectTrain={handleSelectTrain}
            />
          ) : activeNavTab === 'DELAY_PROPAGATION' ? (
            <DelayPropagationView data={propagationData} loading={loadingProp} />
          ) : activeNavTab === 'JUNCTION_RISK' ? (
            <JunctionRiskView
              conflicts={conflicts}
              trains={trains}
              selectedTrainId={selectedTrainId}
              onSelectTrain={handleSelectTrain}
              loading={loadingConflicts}
            />
          ) : activeNavTab === 'FORECAST' ? (
            <ForecastView data={selectedTrainETA} loading={loadingETA} />
          ) : activeNavTab === 'OPERATOR_VIEW' ? (
            <OperatorView
              trains={trains}
              selectedTrain={selectedTrain}
              selectedTrainETA={selectedTrainETA}
              conflicts={conflicts}
              onSelectTrain={handleSelectTrain}
            />
          ) : activeNavTab === 'PASSENGER_VIEW' ? (
            <PassengerCardView
              trains={trains}
              selectedTrainId={selectedTrainId}
              selectedTrain={selectedTrain}
              selectedTrainETA={selectedTrainETA}
              onSelectTrain={handleSelectTrain}
            />
          ) : activeNavTab === 'COMMAND_CENTER' ? (
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <ForecastView data={selectedTrainETA} loading={loadingETA} />
              <div style={{ padding: '0 24px 24px 24px' }}>
                <JunctionRiskView
                  conflicts={conflicts}
                  trains={trains}
                  selectedTrainId={selectedTrainId}
                  onSelectTrain={handleSelectTrain}
                  loading={loadingConflicts}
                />
              </div>
            </div>
          ) : activeNavTab === 'NETWORK_VIEW' ? (
            <div style={{ width: '100%', height: '100%', position: 'relative' }}>
              <RailwayMap
                stations={networkState?.stations || []}
                sections={networkState?.sections || []}
                trains={trains}
                selectedTrain={selectedTrain}
                onSelectTrain={setSelectedTrain}
              />
            </div>
          ) : activeNavTab === 'TIME_SPACE' ? (
            <div style={{ width: '100%', height: '100%', overflowY: 'auto' }}>
              <HistoricalDataDashboard />
            </div>
          ) : (
            <MLStudioView
              simulationState={simulationState}
              networkState={networkState}
              selectedTrain={selectedTrain}
              onSelectTrain={setSelectedTrain}
              coaLogs={coaLogs}
              onStart={startSimulation}
              onPause={pauseSimulation}
              onReset={resetSimulation}
              onSetSpeed={setSimulationSpeed}
              isIncidentModalOpen={isIncidentModalOpen}
              setIsIncidentModalOpen={setIsIncidentModalOpen}
              isMetricsModalOpen={isMetricsModalOpen}
              setIsMetricsModalOpen={setIsMetricsModalOpen}
            />
          )}
        </main>
      </div>

      {/* Switch Train Modal */}
      <SwitchTrainModal
        isOpen={isSwitchModalOpen}
        onClose={() => setIsSwitchModalOpen(false)}
        trains={trains}
        selectedTrainId={selectedTrainId}
        onSelectTrain={handleSelectTrain}
        onSyncTrainNumber={handleSyncTrainNumber}
      />
    </div>
  );
};

export default App;
