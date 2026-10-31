import {
  SimulationState,
  TrainState,
  ETAPrediction,
  ModelMetrics,
  COAEvent,
  TrainRouteResponse,
  CounterfactualRequest,
  CounterfactualResponse,
  TrainETAComparison,
  RankedJunctionConflict,
  DownstreamPropagationResponse,
  CorridorHealthSummary
} from '../types';

const API_BASE_URL = '/api/v1';


export async function fetchTrains(): Promise<TrainState[]> {
  const res = await fetch(`${API_BASE_URL}/trains`);
  if (!res.ok) throw new Error('Failed to fetch trains');
  const data = await res.json();
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.trains)) return data.trains;
  return [];
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

export async function fetchCorridorHealth(): Promise<CorridorHealthSummary> {
  const res = await fetch(`${API_BASE_URL}/corridor/health`);
  if (!res.ok) throw new Error('Failed to fetch corridor health');
  return res.json();
}

export async function fetchTrainETAComparison(trainId: string): Promise<TrainETAComparison> {
  const res = await fetch(`${API_BASE_URL}/corridor/train/${encodeURIComponent(trainId)}/eta-comparison`);
  if (!res.ok) throw new Error(`Failed to fetch ETA comparison for train ${trainId}`);
  return res.json();
}

export async function fetchRankedJunctionConflicts(): Promise<RankedJunctionConflict[]> {
  const res = await fetch(`${API_BASE_URL}/corridor/junctions/conflicts`);
  if (!res.ok) throw new Error('Failed to fetch ranked junction conflicts');
  return res.json();
}

export async function fetchDownstreamPropagation(
  junctionCode?: string,
  trainId?: string
): Promise<DownstreamPropagationResponse> {
  const params = new URLSearchParams();
  if (junctionCode) params.set('junction_code', junctionCode);
  if (trainId) params.set('train_id', trainId);
  const qs = params.toString() ? `?${params.toString()}` : '';
  const res = await fetch(`${API_BASE_URL}/corridor/propagation${qs}`);
  if (!res.ok) throw new Error('Failed to fetch downstream delay propagation');
  return res.json();
}

export async function runCorridorCounterfactual(
  req: CounterfactualRequest
): Promise<CounterfactualResponse> {
  const res = await fetch(`${API_BASE_URL}/corridor/counterfactual`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req)
  });
  if (!res.ok) throw new Error('Failed to run corridor counterfactual simulation');
  return res.json();
}

export async function syncCorridorTrain(trainNumber: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/corridor/sync-train`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ train_number: trainNumber })
  });
  if (!res.ok) throw new Error(`Failed to sync train ${trainNumber}`);
  return res.json();
}

// -------------------------------------------------------------
// Gemma 4 Agent Endpoints
// -------------------------------------------------------------

export async function fetchAgentHealth(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/agent/health`);
  if (!res.ok) throw new Error('Failed to fetch agent health');
  return res.json();
}

export async function runAgentDispatch(payload: {
  train_id?: string;
  alert_id?: string;
  context?: string;
  model?: string;
}): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/agent/dispatch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Agent dispatch reasoning failed');
  return res.json();
}

export async function sendAgentChatMessage(
  sessionId: string | null,
  message: string,
  model?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/agent/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message, model })
  });
  if (!res.ok) throw new Error('Agent chat failed');
  return res.json();
}

export async function fetchAgentExplanation(
  trainId: string,
  context?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/agent/explain`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ train_id: trainId, context })
  });
  if (!res.ok) throw new Error('Agent explainability failed');
  return res.json();
}

export async function fetchAgentAdvisory(
  trainId: string,
  languages: string[] = ['en', 'hi']
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/agent/advisory`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ train_id: trainId, languages })
  });
  if (!res.ok) throw new Error('Agent advisory generation failed');
  return res.json();
}

export async function uploadAgentVision(
  file: File,
  prompt?: string
): Promise<any> {
  const formData = new FormData();
  formData.append('file', file);
  if (prompt) formData.append('prompt', prompt);

  const res = await fetch(`${API_BASE_URL}/agent/vision`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) throw new Error('Agent vision analysis failed');
  return res.json();
}

export async function approveAgentDecision(
  decisionId: string,
  data?: { controller_id?: string; edited_order?: string; notes?: string }
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/agent/decisions/${decisionId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data || {})
  });
  if (!res.ok) throw new Error('Failed to approve decision');
  return res.json();
}

export async function rejectAgentDecision(
  decisionId: string,
  data?: { controller_id?: string; notes?: string }
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/agent/decisions/${decisionId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data || {})
  });
  if (!res.ok) throw new Error('Failed to reject decision');
  return res.json();
}

export async function fetchAgentDecisions(status?: string): Promise<any[]> {
  const qs = status ? `?status=${encodeURIComponent(status)}` : '';
  const res = await fetch(`${API_BASE_URL}/agent/decisions${qs}`);
  if (!res.ok) throw new Error('Failed to fetch decisions');
  return res.json();
}

