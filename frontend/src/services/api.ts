import { SimulationState, TrainState, ETAPrediction, ModelMetrics, COAEvent, TrainRouteResponse, CounterfactualRequest, CounterfactualResponse } from '../types';

const API_BASE_URL = '/api/v1';


export async function fetchTrains(): Promise<TrainState[]> {
  const res = await fetch(`${API_BASE_URL}/trains`);
  if (!res.ok) throw new Error('Failed to fetch trains');
  return res.json();
}

export async function fetchTrainDetails(trainId: string): Promise<TrainState> {
  const res = await fetch(`${API_BASE_URL}/trains/${trainId}`);
  if (!res.ok) throw new Error('Failed to fetch train details');
  return res.json();
}

export async function fetchTrainETA(trainId: string): Promise<ETAPrediction> {
  const res = await fetch(`${API_BASE_URL}/trains/${trainId}/eta`);
  if (!res.ok) throw new Error('Failed to fetch ETA');
  return res.json();
}

export async function fetchTrainRoute(trainId: string, date?: string): Promise<TrainRouteResponse> {
  const query = date ? `?journey_date=${encodeURIComponent(date)}` : '';
  const res = await fetch(`${API_BASE_URL}/trains/${trainId}/route${query}`);
  if (!res.ok) throw new Error('Failed to fetch train route timeline');
  return res.json();
}

export async function runCounterfactualSimulation(req: CounterfactualRequest): Promise<CounterfactualResponse> {
  const res = await fetch(`${API_BASE_URL}/counterfactual/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req)
  });
  if (!res.ok) throw new Error('Failed to run counterfactual simulation');
  return res.json();
}

export async function fetchNetworkState() {
  const res = await fetch(`${API_BASE_URL}/network/state`);
  if (!res.ok) throw new Error('Failed to fetch network state');
  return res.json();
}

export async function fetchModelMetrics(): Promise<ModelMetrics> {
  const res = await fetch(`${API_BASE_URL}/model/metrics`);
  if (!res.ok) throw new Error('Failed to fetch model metrics');
  return res.json();
}

export async function triggerModelRetrain(): Promise<{ status: string; metrics: ModelMetrics }> {
  const res = await fetch(`${API_BASE_URL}/model/retrain`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to trigger model retraining');
  return res.json();
}

export async function fetchCOAEvents(): Promise<COAEvent[]> {
  const res = await fetch(`${API_BASE_URL}/events/coa`);
  if (!res.ok) throw new Error('Failed to fetch COA events');
  return res.json();
}

export async function startSimulation() {
  const res = await fetch(`${API_BASE_URL}/simulation/start`, { method: 'POST' });
  return res.json();
}

export async function pauseSimulation() {
  const res = await fetch(`${API_BASE_URL}/simulation/pause`, { method: 'POST' });
  return res.json();
}

export async function resetSimulation() {
  const res = await fetch(`${API_BASE_URL}/simulation/reset`, { method: 'POST' });
  return res.json();
}

export async function setSimulationSpeed(multiplier: number) {
  const res = await fetch(`${API_BASE_URL}/simulation/speed`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ speed_multiplier: multiplier })
  });
  return res.json();
}

export async function triggerSIHDemoStep() {
  const res = await fetch(`${API_BASE_URL}/simulation/demo_step`, { method: 'POST' });
  return res.json();
}

export async function injectIncident(data: {
  event_type: string;
  section_id: string;
  severity?: string;
  duration_minutes?: number;
  visibility_meters?: number;
}) {
  const res = await fetch(`${API_BASE_URL}/events/inject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function clearAllIncidents() {
  const res = await fetch(`${API_BASE_URL}/events/clear`, { method: 'POST' });
  return res.json();
}

export async function fetchDataSourceStatus() {
  const res = await fetch(`${API_BASE_URL}/data/source/status`);
  if (!res.ok) throw new Error('Failed to fetch data source status');
  return res.json();
}

export async function fetchFeatureImportance() {
  const res = await fetch(`${API_BASE_URL}/ml/model/feature-importance`);
  if (!res.ok) throw new Error('Failed to fetch feature importance');
  return res.json();
}

export async function fetchVersionHistory() {
  const res = await fetch(`${API_BASE_URL}/ml/model/history`);
  if (!res.ok) throw new Error('Failed to fetch model version history');
  return res.json();
}

export async function fetchSystemHealth() {
  const res = await fetch(`${API_BASE_URL}/system/health`);
  if (!res.ok) throw new Error('Failed to fetch system health');
  return res.json();
}

export async function fetchSectionDelays() {
  const res = await fetch(`${API_BASE_URL}/analytics/section-delays`);
  if (!res.ok) throw new Error('Failed to fetch section delays');
  return res.json();
}
