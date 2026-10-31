import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Terminal, Cpu, Database, CheckCircle2, Sliders } from 'lucide-react';
import { AgentToolTrace } from '../../types';

interface AgentTraceProps {
  trace?: AgentToolTrace[];
}

export const AgentTrace: React.FC<AgentTraceProps> = ({ trace = [] }) => {
  const [expandedSteps, setExpandedSteps] = useState<Record<number, boolean>>({});
  const [showAll, setShowAll] = useState<boolean>(true);

  if (!trace || trace.length === 0) {
    return (
      <div
        style={{
          padding: '16px',
          backgroundColor: '#071224',
          borderRadius: '8px',
          border: '1px dashed #1e3a6a',
          color: '#64748b',
          fontSize: '0.82rem',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}
      >
        <Terminal size={16} />
        <span>No tool execution trace recorded yet. Run an analysis to inspect tool execution steps.</span>
      </div>
    );
  }

  const toggleStep = (stepIdx: number) => {
    setExpandedSteps((prev) => ({
      ...prev,
      [stepIdx]: prev[stepIdx] !== undefined ? !prev[stepIdx] : !showAll
    }));
  };

  const toggleExpandAll = () => {
    const nextState = !showAll;
    setShowAll(nextState);
    const updated: Record<number, boolean> = {};
    trace.forEach((_, idx) => {
      updated[idx] = nextState;
    });
    setExpandedSteps(updated);
  };

  const getToolColor = (toolName: string) => {
    if (toolName.includes('counterfactual')) return { bg: '#3b0764', border: '#7e22ce', text: '#d8b4fe' };
    if (toolName.includes('conflict')) return { bg: '#450a0a', border: '#dc2626', text: '#fca5a5' };
    if (toolName.includes('rulebook')) return { bg: '#451a03', border: '#d97706', text: '#fcd34d' };
    if (toolName.includes('prediction') || toolName.includes('importance')) return { bg: '#042f2e', border: '#0d9488', text: '#5eead4' };
    if (toolName.includes('headway') || toolName.includes('topology')) return { bg: '#0c4a6e', border: '#0284c7', text: '#7dd3fc' };
    return { bg: '#172554', border: '#2563eb', text: '#93c5fd' };
  };

  return (
    <div
      style={{
        backgroundColor: '#071224',
        borderRadius: '8px',
        border: '1px solid #172e54',
        padding: '14px',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px'
      }}
    >
      {/* Header bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #14284b',
          paddingBottom: '8px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Cpu size={16} color="#38bdf8" />
          <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f8fafc' }}>
            Simulation Tool Execution Trace
          </span>
          <span
            style={{
              padding: '2px 8px',
              borderRadius: '12px',
              backgroundColor: '#0369a1',
              color: '#ffffff',
              fontSize: '0.7rem',
              fontWeight: 700
            }}
          >
            {trace.length} {trace.length === 1 ? 'Step' : 'Steps'}
          </span>
        </div>
        <button
          onClick={toggleExpandAll}
          style={{
            background: 'none',
            border: 'none',
            color: '#38bdf8',
            fontSize: '0.72rem',
            cursor: 'pointer',
            textDecoration: 'underline'
          }}
        >
          {showAll ? 'Collapse All' : 'Expand All'}
        </button>
      </div>

      {/* Step items */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {trace.map((item, idx) => {
          const isExpanded = expandedSteps[idx] !== undefined ? expandedSteps[idx] : showAll;
          const colors = getToolColor(item.tool);
          const hasError = item.result && item.result.error;

          return (
            <div
              key={idx}
              style={{
                backgroundColor: '#09152b',
                borderRadius: '6px',
                border: `1px solid ${hasError ? '#dc2626' : '#172e54'}`,
                overflow: 'hidden'
              }}
            >
              {/* Accordion trigger */}
              <div
                onClick={() => toggleStep(idx)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '8px 12px',
                  cursor: 'pointer',
                  backgroundColor: '#0c1a35'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {isExpanded ? <ChevronDown size={14} color="#94a3b8" /> : <ChevronRight size={14} color="#94a3b8" />}
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>
                    Step {item.step || idx + 1}:
                  </span>
                  <span
                    style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      backgroundColor: colors.bg,
                      border: `1px solid ${colors.border}`,
                      color: colors.text,
                      fontSize: '0.72rem',
                      fontFamily: 'monospace',
                      fontWeight: 700
                    }}
                  >
                    {item.tool}()
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {hasError ? (
                    <span style={{ fontSize: '0.68rem', color: '#ef4444', fontWeight: 600 }}>Error Handled</span>
                  ) : (
                    <span style={{ fontSize: '0.68rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <CheckCircle2 size={12} color="#10b981" /> Computed
                    </span>
                  )}
                </div>
              </div>

              {/* Accordion Body */}
              {isExpanded && (
                <div style={{ padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {/* Tool Args */}
                  <div>
                    <div
                      style={{
                        fontSize: '0.68rem',
                        fontWeight: 700,
                        color: '#94a3b8',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px',
                        marginBottom: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                    >
                      <Sliders size={12} />
                      Arguments Passed to Engine:
                    </div>
                    <pre
                      style={{
                        margin: 0,
                        padding: '8px',
                        backgroundColor: '#050b17',
                        borderRadius: '4px',
                        border: '1px solid #14284b',
                        color: '#e2e8f0',
                        fontSize: '0.72rem',
                        fontFamily: 'Consolas, Monaco, monospace',
                        overflowX: 'auto',
                        whiteSpace: 'pre-wrap'
                      }}
                    >
                      {JSON.stringify(item.args || {}, null, 2)}
                    </pre>
                  </div>

                  {/* Engine Result */}
                  <div>
                    <div
                      style={{
                        fontSize: '0.68rem',
                        fontWeight: 700,
                        color: '#94a3b8',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px',
                        marginBottom: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                    >
                      <Database size={12} />
                      Simulated Ground Truth Output:
                    </div>
                    <pre
                      style={{
                        margin: 0,
                        padding: '8px',
                        backgroundColor: '#050b17',
                        borderRadius: '4px',
                        border: '1px solid #14284b',
                        color: '#38bdf8',
                        fontSize: '0.72rem',
                        fontFamily: 'Consolas, Monaco, monospace',
                        maxHeight: '160px',
                        overflowY: 'auto',
                        whiteSpace: 'pre-wrap'
                      }}
                    >
                      {JSON.stringify(item.result || {}, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
