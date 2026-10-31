import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Bot,
  Play,
  CheckCircle,
  XCircle,
  Edit3,
  BookOpen,
  ArrowRight,
  TrendingDown,
  Sparkles,
  Camera,
  RotateCw,
  Loader2,
  FileText,
  Clock,
  AlertCircle
} from 'lucide-react';
import {
  runAgentDispatch,
  approveAgentDecision,
  rejectAgentDecision,
  fetchAgentDecisions,
  fetchAgentHealth
} from '../../services/api';
import {
  TrainState,
  RankedJunctionConflict,
  AgentDispatchResponse,
  AgentDecisionRecord
} from '../../types';
import { AgentTrace } from './AgentTrace';
import { VisionAnalysisModal } from './VisionAnalysisModal';

interface DispatcherCopilotProps {
  trains: TrainState[];
  selectedTrainId: string;
  conflicts: RankedJunctionConflict[];
  onSelectTrain: (trainId: string) => void;
}

export const DispatcherCopilot: React.FC<DispatcherCopilotProps> = ({
  trains,
  selectedTrainId,
  conflicts,
  onSelectTrain
}) => {
  const [selectedAlertId, setSelectedAlertId] = useState<string>('');
  const [contextInput, setContextInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [dispatchResult, setDispatchResult] = useState<AgentDispatchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Health & Model status
  const [healthInfo, setHealthInfo] = useState<{ status: string; backend: string; model?: string } | null>(null);

  // Edit order state
  const [isEditingOrder, setIsEditingOrder] = useState<boolean>(false);
  const [editedOrder, setEditedOrder] = useState<string>('');
  const [controllerNotes, setControllerNotes] = useState<string>('');
  const [controllerId, setControllerId] = useState<string>('CTRL_DELHI_DIV_04');

  // Approval status state
  const [decisionStatus, setDecisionStatus] = useState<'PENDING' | 'APPROVED' | 'REJECTED'>('PENDING');
  const [actionInProgress, setActionInProgress] = useState<boolean>(false);

  // Recent decisions
  const [recentDecisions, setRecentDecisions] = useState<AgentDecisionRecord[]>([]);

  // Vision Modal
  const [isVisionOpen, setIsVisionOpen] = useState<boolean>(false);

  useEffect(() => {
    fetchAgentHealth()
      .then((h) => setHealthInfo(h))
      .catch(() => setHealthInfo({ status: 'offline', backend: 'fallback' }));

    loadDecisions();
  }, []);

  const loadDecisions = () => {
    fetchAgentDecisions()
      .then((decs) => setRecentDecisions(decs || []))
      .catch(() => {});
  };

  const handleRunDispatch = async () => {
    setLoading(true);
    setError(null);
    setDispatchResult(null);
    setIsEditingOrder(false);
    setDecisionStatus('PENDING');

    try {
      const payload: any = {
        train_id: selectedTrainId,
        context: contextInput.trim() || undefined
      };
      if (selectedAlertId) {
        payload.alert_id = selectedAlertId;
      }

      const res = await runAgentDispatch(payload);
      setDispatchResult(res);
      setEditedOrder(res.operating_order_draft || '');
      loadDecisions();
    } catch (err: any) {
      setError(err.message || 'Dispatch reasoning failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!dispatchResult) return;
    setActionInProgress(true);
    try {
      const decisionId = dispatchResult.decision_id || 'latest';
      await approveAgentDecision(decisionId, {
        controller_id: controllerId,
        edited_order: isEditingOrder ? editedOrder : undefined,
        notes: controllerNotes
      });
      setDecisionStatus('APPROVED');
      loadDecisions();
    } catch (err: any) {
      setError(err.message || 'Approval failed.');
    } finally {
      setActionInProgress(false);
    }
  };

  const handleReject = async () => {
    if (!dispatchResult) return;
    setActionInProgress(true);
    try {
      const decisionId = dispatchResult.decision_id || 'latest';
      await rejectAgentDecision(decisionId, {
        controller_id: controllerId,
        notes: controllerNotes || 'Rejected by controller review'
      });
      setDecisionStatus('REJECTED');
      loadDecisions();
    } catch (err: any) {
      setError(err.message || 'Rejection failed.');
    } finally {
      setActionInProgress(false);
    }
  };

  const handleVisionImport = (facts: any) => {
    const formatted = `Visual Import Facts: ${JSON.stringify(facts)}`;
    setContextInput((prev) => (prev ? `${prev}\n${formatted}` : formatted));
  };

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* 1. Header Bar with Gemma 4 Badge & Vision upload trigger */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
          borderBottom: '1px solid #14284b',
          paddingBottom: '16px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              backgroundColor: '#0284c7',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 14px rgba(2, 132, 199, 0.4)'
            }}
          >
            <Bot size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1.2rem', fontWeight: 800, color: '#f8fafc' }}>
                AI Dispatcher Copilot
              </span>
              {/* Powered by Gemma 4 Badge */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '3px 10px',
                  borderRadius: '20px',
                  backgroundColor: dispatchResult?.source === 'fallback' ? '#451a03' : '#042f2e',
                  border: `1px solid ${dispatchResult?.source === 'fallback' ? '#d97706' : '#0d9488'}`,
                  color: dispatchResult?.source === 'fallback' ? '#fcd34d' : '#5eead4',
                  fontSize: '0.72rem',
                  fontWeight: 700
                }}
              >
                <Sparkles size={12} />
                <span>
                  Powered by Gemma 4{' '}
                  {dispatchResult?.source === 'fallback'
                    ? '(Fallback Mode)'
                    : `(${healthInfo?.model || 'gemma-4-31b-it'})`}
                </span>
              </div>
            </div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>
              Autonomous candidate counterfactual testing, rulebook retrieval, and grounded operating orders.
            </div>
          </div>
        </div>

        {/* Action controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={() => setIsVisionOpen(true)}
            style={{
              padding: '8px 14px',
              borderRadius: '6px',
              backgroundColor: '#0b1e3b',
              border: '1px solid #1e3a6a',
              color: '#38bdf8',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Camera size={15} />
            <span>Upload Display / Diagram</span>
          </button>
        </div>
      </div>

      {/* 2. Dispatch Configuration & Trigger Section */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '16px',
          backgroundColor: '#071224',
          padding: '18px',
          borderRadius: '10px',
          border: '1px solid #14284b'
        }}
      >
        {/* Train Selector */}
        <div>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#94a3b8', marginBottom: '6px' }}>
            Target Train:
          </label>
          <select
            value={selectedTrainId}
            onChange={(e) => onSelectTrain(e.target.value)}
            style={{
              width: '100%',
              padding: '9px 12px',
              backgroundColor: '#050b17',
              border: '1px solid #1e3a6a',
              borderRadius: '6px',
              color: '#f8fafc',
              fontSize: '0.82rem',
              outline: 'none'
            }}
          >
            {trains.map((t) => (
              <option key={t.train_id} value={t.train_number}>
                {t.train_number} - {t.train_name} ({t.current_delay_minutes}m delay)
              </option>
            ))}
          </select>
        </div>

        {/* Conflict / Alert Link */}
        <div>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#94a3b8', marginBottom: '6px' }}>
            Active Corridor Alert / Conflict:
          </label>
          <select
            value={selectedAlertId}
            onChange={(e) => setSelectedAlertId(e.target.value)}
            style={{
              width: '100%',
              padding: '9px 12px',
              backgroundColor: '#050b17',
              border: '1px solid #1e3a6a',
              borderRadius: '6px',
              color: '#f8fafc',
              fontSize: '0.82rem',
              outline: 'none'
            }}
          >
            <option value="">No Alert Selected (Auto-Triage)</option>
            {conflicts.map((c) => (
              <option key={c.station_id || c.station_code} value={c.station_code}>
                {c.station_name} ({c.station_code}) - Risk: {c.risk_level} ({c.approaching_trains_count || 0} trains)
              </option>
            ))}
          </select>
        </div>

        {/* Custom Context or Overrides */}
        <div style={{ gridColumn: 'span 2' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#94a3b8', marginBottom: '6px' }}>
            Operational Context / Controller Directives:
          </label>
          <input
            type="text"
            value={contextInput}
            onChange={(e) => setContextInput(e.target.value)}
            placeholder="e.g. Fog restriction 60km/h near MTJ, or hold 12951 at Mathura for freight clearance..."
            style={{
              width: '100%',
              padding: '9px 12px',
              backgroundColor: '#050b17',
              border: '1px solid #1e3a6a',
              borderRadius: '6px',
              color: '#f8fafc',
              fontSize: '0.82rem',
              outline: 'none',
              boxSizing: 'border-box'
            }}
          />
        </div>

        {/* Run Button */}
        <div style={{ gridColumn: 'span 2', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button
            onClick={handleRunDispatch}
            disabled={loading}
            style={{
              padding: '11px 24px',
              borderRadius: '6px',
              backgroundColor: loading ? '#0369a1' : '#0284c7',
              color: '#ffffff',
              border: 'none',
              fontSize: '0.85rem',
              fontWeight: 700,
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 4px 14px rgba(2, 132, 199, 0.4)',
              transition: 'background-color 0.2s'
            }}
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Gemma 4 Reasoning & Simulating Counterfactuals...</span>
              </>
            ) : (
              <>
                <Play size={16} />
                <span>Analyze with Gemma 4</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div
          style={{
            padding: '12px 16px',
            backgroundColor: '#450a0a',
            border: '1px solid #dc2626',
            borderRadius: '8px',
            color: '#fca5a5',
            fontSize: '0.82rem',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}
        >
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* 3. Dispatch Recommendation Display */}
      {dispatchResult && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Main Card */}
          <div
            style={{
              backgroundColor: '#071224',
              borderRadius: '10px',
              border: '1px solid #172e54',
              overflow: 'hidden'
            }}
          >
            {/* Card Header */}
            <div
              style={{
                padding: '14px 18px',
                backgroundColor: '#0c1a35',
                borderBottom: '1px solid #14284b',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '8px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <FileText size={18} color="#38bdf8" />
                <span style={{ fontSize: '0.92rem', fontWeight: 800, color: '#f8fafc' }}>
                  Gemma 4 Dispatch Directive
                </span>
                {/* Confidence badge */}
                <span
                  style={{
                    padding: '2px 8px',
                    borderRadius: '4px',
                    backgroundColor:
                      dispatchResult.confidence === 'high'
                        ? '#064e3b'
                        : dispatchResult.confidence === 'medium'
                        ? '#78350f'
                        : '#7f1d1d',
                    color:
                      dispatchResult.confidence === 'high'
                        ? '#6ee7b7'
                        : dispatchResult.confidence === 'medium'
                        ? '#fde68a'
                        : '#fca5a5',
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    textTransform: 'uppercase'
                  }}
                >
                  {dispatchResult.confidence || 'HIGH'} CONFIDENCE
                </span>
              </div>

              {/* Status Indicator */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Decision Status:</span>
                <span
                  style={{
                    padding: '3px 10px',
                    borderRadius: '12px',
                    backgroundColor:
                      decisionStatus === 'APPROVED'
                        ? '#064e3b'
                        : decisionStatus === 'REJECTED'
                        ? '#7f1d1d'
                        : '#1e3a8a',
                    color:
                      decisionStatus === 'APPROVED'
                        ? '#6ee7b7'
                        : decisionStatus === 'REJECTED'
                        ? '#fca5a5'
                        : '#93c5fd',
                    fontSize: '0.72rem',
                    fontWeight: 800
                  }}
                >
                  {decisionStatus}
                </span>
              </div>
            </div>

            {/* Recommendation Body */}
            <div style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Summary */}
              <div style={{ fontSize: '0.86rem', color: '#e2e8f0', lineHeight: 1.5 }}>
                {dispatchResult.summary}
              </div>

              {/* Core Intervention Metrics Banner */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '12px',
                  backgroundColor: '#09152b',
                  padding: '14px',
                  borderRadius: '8px',
                  border: '1px solid #14284b'
                }}
              >
                <div>
                  <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase' }}>
                    Recommended Action
                  </div>
                  <div style={{ fontSize: '0.98rem', fontWeight: 800, color: '#38bdf8', marginTop: '4px' }}>
                    {dispatchResult.recommendation?.action || 'REGULATE'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase' }}>
                    Target Train
                  </div>
                  <div style={{ fontSize: '0.98rem', fontWeight: 800, color: '#f8fafc', marginTop: '4px' }}>
                    {dispatchResult.recommendation?.train_id || selectedTrainId}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase' }}>
                    Passenger-Minutes Saved
                  </div>
                  <div
                    style={{
                      fontSize: '0.98rem',
                      fontWeight: 800,
                      color: '#10b981',
                      marginTop: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    <TrendingDown size={16} />
                    <span>+{dispatchResult.recommendation?.expected_passenger_minutes_saved || 0} min</span>
                  </div>
                </div>
              </div>

              {/* Alternatives Considered */}
              {dispatchResult.alternatives_considered && dispatchResult.alternatives_considered.length > 0 && (
                <div>
                  <div
                    style={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      color: '#94a3b8',
                      textTransform: 'uppercase',
                      marginBottom: '8px'
                    }}
                  >
                    Counterfactual Alternatives Tested by Agent:
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {dispatchResult.alternatives_considered.map((alt, idx) => (
                      <div
                        key={idx}
                        style={{
                          padding: '8px 12px',
                          backgroundColor: '#09152b',
                          borderRadius: '6px',
                          border: '1px solid #14284b',
                          fontSize: '0.78rem',
                          color: '#cbd5e1',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <ArrowRight size={14} color="#64748b" />
                          <span style={{ fontWeight: 600 }}>{alt.action}</span>
                        </div>
                        <span style={{ color: '#94a3b8', fontFamily: 'monospace' }}>
                          {JSON.stringify(alt.result)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Rulebook Citations */}
              {dispatchResult.rule_citations && dispatchResult.rule_citations.length > 0 && (
                <div>
                  <div
                    style={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      color: '#94a3b8',
                      textTransform: 'uppercase',
                      marginBottom: '8px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}
                  >
                    <BookOpen size={14} color="#f59e0b" />
                    <span>Indian Railways Operating Rule Citations:</span>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {dispatchResult.rule_citations.map((rule, idx) => (
                      <span
                        key={idx}
                        style={{
                          padding: '4px 10px',
                          backgroundColor: '#451a03',
                          border: '1px solid #d97706',
                          borderRadius: '4px',
                          color: '#fde68a',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          fontFamily: 'monospace'
                        }}
                      >
                        {rule}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Operating Order Draft (with Edit mode) */}
              <div>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '8px'
                  }}
                >
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase' }}>
                    Formal Operating Order Draft:
                  </span>
                  <button
                    onClick={() => setIsEditingOrder(!isEditingOrder)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#38bdf8',
                      fontSize: '0.75rem',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    <Edit3 size={13} />
                    <span>{isEditingOrder ? 'Lock Draft' : 'Edit Draft'}</span>
                  </button>
                </div>

                {isEditingOrder ? (
                  <textarea
                    rows={4}
                    value={editedOrder}
                    onChange={(e) => setEditedOrder(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      backgroundColor: '#050b17',
                      border: '1px solid #0284c7',
                      borderRadius: '6px',
                      color: '#f8fafc',
                      fontSize: '0.82rem',
                      fontFamily: 'Consolas, Monaco, monospace',
                      outline: 'none',
                      boxSizing: 'border-box'
                    }}
                  />
                ) : (
                  <div
                    style={{
                      padding: '12px 14px',
                      backgroundColor: '#050b17',
                      border: '1px solid #14284b',
                      borderRadius: '6px',
                      color: '#e2e8f0',
                      fontSize: '0.82rem',
                      fontFamily: 'Consolas, Monaco, monospace',
                      lineHeight: 1.5,
                      whiteSpace: 'pre-wrap'
                    }}
                  >
                    {editedOrder || dispatchResult.operating_order_draft}
                  </div>
                )}
              </div>

              {/* Controller Notes & HITL Approval Bar */}
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px',
                  backgroundColor: '#09152b',
                  padding: '14px',
                  borderRadius: '8px',
                  border: '1px solid #1e3a6a'
                }}
              >
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                  <input
                    type="text"
                    value={controllerNotes}
                    onChange={(e) => setControllerNotes(e.target.value)}
                    placeholder="Controller review notes (optional, e.g. Confirmed with Kota section controller)..."
                    style={{
                      flex: 1,
                      padding: '8px 12px',
                      backgroundColor: '#050b17',
                      border: '1px solid #14284b',
                      borderRadius: '6px',
                      color: '#f8fafc',
                      fontSize: '0.78rem',
                      outline: 'none'
                    }}
                  />
                  <input
                    type="text"
                    value={controllerId}
                    onChange={(e) => setControllerId(e.target.value)}
                    title="Controller ID"
                    style={{
                      width: '180px',
                      padding: '8px 12px',
                      backgroundColor: '#050b17',
                      border: '1px solid #14284b',
                      borderRadius: '6px',
                      color: '#94a3b8',
                      fontSize: '0.75rem',
                      fontFamily: 'monospace',
                      outline: 'none'
                    }}
                  />
                </div>

                {/* Approve / Reject Buttons */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                  <button
                    onClick={handleReject}
                    disabled={actionInProgress || decisionStatus === 'REJECTED'}
                    style={{
                      padding: '8px 18px',
                      backgroundColor: decisionStatus === 'REJECTED' ? '#450a0a' : '#7f1d1d',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '0.8rem',
                      fontWeight: 700,
                      cursor: actionInProgress || decisionStatus === 'REJECTED' ? 'not-allowed' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}
                  >
                    <XCircle size={15} />
                    <span>Reject Order</span>
                  </button>

                  <button
                    onClick={handleApprove}
                    disabled={actionInProgress || decisionStatus === 'APPROVED'}
                    style={{
                      padding: '8px 20px',
                      backgroundColor: decisionStatus === 'APPROVED' ? '#064e3b' : '#059669',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '0.8rem',
                      fontWeight: 700,
                      cursor: actionInProgress || decisionStatus === 'APPROVED' ? 'not-allowed' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      boxShadow: '0 2px 10px rgba(5, 150, 105, 0.3)'
                    }}
                  >
                    <CheckCircle size={15} />
                    <span>{decisionStatus === 'APPROVED' ? 'Order Approved' : 'Approve Order'}</span>
                  </button>
                </div>
              </div>

              {/* Mandatory AI Disclaimer */}
              <div
                style={{
                  padding: '8px 12px',
                  backgroundColor: '#0c1a35',
                  borderRadius: '6px',
                  border: '1px solid #1e3a6a',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  color: '#94a3b8',
                  fontSize: '0.72rem'
                }}
              >
                <ShieldAlert size={15} color="#38bdf8" />
                <span>
                  <strong>AI-generated, controller must verify:</strong> Numerical claims and delay impacts are
                  grounded in CounterfactualSimulator. Operating decisions require human sign-off prior to transmission.
                </span>
              </div>
            </div>
          </div>

          {/* 4. Expandable Agent Trace */}
          <AgentTrace trace={dispatchResult.tool_trace} />
        </div>
      )}

      {/* 5. Historical / Recent Decisions Table */}
      {recentDecisions.length > 0 && (
        <div
          style={{
            backgroundColor: '#071224',
            borderRadius: '10px',
            border: '1px solid #14284b',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Clock size={16} color="#38bdf8" />
              <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f8fafc' }}>
                Controller Decision Audit Log
              </span>
            </div>
            <button
              onClick={loadDecisions}
              style={{
                background: 'none',
                border: 'none',
                color: '#38bdf8',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '0.72rem'
              }}
            >
              <RotateCw size={12} />
              <span>Refresh Log</span>
            </button>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #14284b', textAlign: 'left', color: '#64748b' }}>
                  <th style={{ padding: '6px 8px' }}>ID</th>
                  <th style={{ padding: '6px 8px' }}>Train</th>
                  <th style={{ padding: '6px 8px' }}>Action</th>
                  <th style={{ padding: '6px 8px' }}>Status</th>
                  <th style={{ padding: '6px 8px' }}>Controller</th>
                  <th style={{ padding: '6px 8px' }}>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {recentDecisions.slice(0, 5).map((d) => (
                  <tr key={d.id} style={{ borderBottom: '1px solid #0c1a35', color: '#cbd5e1' }}>
                    <td style={{ padding: '6px 8px', fontFamily: 'monospace' }}>{d.id.slice(0, 8)}...</td>
                    <td style={{ padding: '6px 8px', fontWeight: 600 }}>{d.train_id}</td>
                    <td style={{ padding: '6px 8px', color: '#38bdf8' }}>{d.action}</td>
                    <td style={{ padding: '6px 8px' }}>
                      <span
                        style={{
                          padding: '2px 6px',
                          borderRadius: '4px',
                          backgroundColor:
                            d.status === 'APPROVED'
                              ? '#064e3b'
                              : d.status === 'REJECTED'
                              ? '#7f1d1d'
                              : '#1e3a8a',
                          color:
                            d.status === 'APPROVED'
                              ? '#6ee7b7'
                              : d.status === 'REJECTED'
                              ? '#fca5a5'
                              : '#93c5fd',
                          fontWeight: 700,
                          fontSize: '0.68rem'
                        }}
                      >
                        {d.status}
                      </span>
                    </td>
                    <td style={{ padding: '6px 8px', color: '#94a3b8' }}>{d.controller_id || 'System'}</td>
                    <td style={{ padding: '6px 8px', color: '#64748b' }}>
                      {d.created_at ? new Date(d.created_at).toLocaleTimeString() : 'Recent'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Vision Modal */}
      <VisionAnalysisModal
        isOpen={isVisionOpen}
        onClose={() => setIsVisionOpen(false)}
        onConfirmFacts={handleVisionImport}
      />
    </div>
  );
};
