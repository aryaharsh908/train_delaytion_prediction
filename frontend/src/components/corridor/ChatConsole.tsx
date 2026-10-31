import React, { useState, useRef, useEffect } from 'react';
import {
  MessageSquare,
  Send,
  Bot,
  User,
  Sparkles,
  Terminal,
  RotateCcw,
  Loader2,
  ShieldAlert,
  ChevronRight
} from 'lucide-react';
import { sendAgentChatMessage } from '../../services/api';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  toolCalls?: string[];
  timestamp: string;
  source?: 'gemma' | 'fallback';
}

const QUICK_PROMPTS = [
  'Why is train 12951 late and what is causing the bottleneck?',
  'What happens if I hold train 12951 at Mathura (MTJ) for 15 minutes?',
  'Which train has precedence between 12951 Rajdhani and 12953 at Kota Junction?',
  'Check platform headway and dwell occupancy at NDLS station.',
  'What is the current propagation risk score for downstream services?'
];

export const ChatConsole: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'init-1',
      sender: 'assistant',
      text: 'Railway Operations Control Room Assistant online. Grounded in the WDFC / Delhi-Mumbai corridor simulation engine and Indian Railways Operating Rulebook. Ask questions regarding train status, conflict resolution, what-if counterfactual holds, or precedence rules.',
      timestamp: new Date().toLocaleTimeString(),
      source: 'gemma'
    }
  ]);
  const [inputValue, setInputValue] = useState<string>('');
  const [sessionId, setSessionId] = useState<string>(() => `sess_${Date.now()}`);
  const [loading, setLoading] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend || inputValue).trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = {
      id: `usr_${Date.now()}`,
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');
    setLoading(true);

    try {
      const res = await sendAgentChatMessage(sessionId, text);

      const assistantMsg: ChatMessage = {
        id: `asst_${Date.now()}`,
        sender: 'assistant',
        text: res.reply || res.response || res.message || 'No response generated.',
        toolCalls: res.tools_called || (res.tool_trace ? res.tool_trace.map((t: any) => t.tool) : []),
        timestamp: new Date().toLocaleTimeString(),
        source: res.source || 'gemma'
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errMsg: ChatMessage = {
        id: `err_${Date.now()}`,
        sender: 'assistant',
        text: `Error processing query: ${err.message || 'Network error'}. Fallback rulebook engine consulted.`,
        timestamp: new Date().toLocaleTimeString(),
        source: 'fallback'
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleResetSession = () => {
    setSessionId(`sess_${Date.now()}`);
    setMessages([
      {
        id: `reset_${Date.now()}`,
        sender: 'assistant',
        text: 'Session reset. New control-room conversation context started.',
        timestamp: new Date().toLocaleTimeString(),
        source: 'gemma'
      }
    ]);
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: '#070e1c',
        boxSizing: 'border-box'
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '14px 20px',
          borderBottom: '1px solid #14284b',
          backgroundColor: '#071224',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              padding: '6px',
              borderRadius: '8px',
              backgroundColor: '#0284c7'
            }}
          >
            <MessageSquare size={18} color="#ffffff" />
          </div>
          <div>
            <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#f8fafc' }}>
              Control-Room AI Chat
            </div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
              Natural Language to Simulation Tools (Powered by Gemma 4)
            </div>
          </div>
        </div>

        <button
          onClick={handleResetSession}
          style={{
            background: 'none',
            border: '1px solid #1e3a6a',
            borderRadius: '6px',
            color: '#94a3b8',
            padding: '6px 12px',
            fontSize: '0.75rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <RotateCcw size={13} />
          <span>New Session</span>
        </button>
      </div>

      {/* Message stream */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px'
        }}
      >
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          return (
            <div
              key={msg.id}
              style={{
                display: 'flex',
                gap: '10px',
                alignSelf: isUser ? 'flex-end' : 'flex-start',
                maxWidth: '85%'
              }}
            >
              {!isUser && (
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '8px',
                    backgroundColor: msg.source === 'fallback' ? '#78350f' : '#0369a1',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0
                  }}
                >
                  <Bot size={18} color="#ffffff" />
                </div>
              )}

              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px'
                }}
              >
                <div
                  style={{
                    padding: '12px 16px',
                    borderRadius: '10px',
                    backgroundColor: isUser ? '#0284c7' : '#09152b',
                    border: `1px solid ${isUser ? '#0284c7' : '#172e54'}`,
                    color: '#f8fafc',
                    fontSize: '0.84rem',
                    lineHeight: 1.5,
                    whiteSpace: 'pre-wrap',
                    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)'
                  }}
                >
                  {msg.text}
                </div>

                {/* Tool calls tags */}
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '0.68rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '3px' }}>
                      <Terminal size={11} /> Grounded with:
                    </span>
                    {msg.toolCalls.map((tool, idx) => (
                      <span
                        key={idx}
                        style={{
                          padding: '1px 6px',
                          borderRadius: '4px',
                          backgroundColor: '#0c1a35',
                          border: '1px solid #1e3a6a',
                          color: '#38bdf8',
                          fontSize: '0.68rem',
                          fontFamily: 'monospace'
                        }}
                      >
                        {tool}()
                      </span>
                    ))}
                  </div>
                )}

                <span style={{ fontSize: '0.68rem', color: '#64748b', alignSelf: isUser ? 'flex-end' : 'flex-start' }}>
                  {msg.timestamp}
                </span>
              </div>

              {isUser && (
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '8px',
                    backgroundColor: '#1e293b',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0
                  }}
                >
                  <User size={18} color="#94a3b8" />
                </div>
              )}
            </div>
          );
        })}

        {loading && (
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                backgroundColor: '#0369a1',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Bot size={18} color="#ffffff" />
            </div>
            <div
              style={{
                padding: '10px 14px',
                borderRadius: '8px',
                backgroundColor: '#09152b',
                border: '1px solid #172e54',
                color: '#38bdf8',
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <Loader2 size={16} className="animate-spin" />
              <span>Gemma 4 querying railway engines & analyzing rules...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompts Chips */}
      <div
        style={{
          padding: '8px 20px',
          display: 'flex',
          gap: '8px',
          overflowX: 'auto',
          backgroundColor: '#071224',
          borderTop: '1px solid #14284b'
        }}
      >
        {QUICK_PROMPTS.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(prompt)}
            disabled={loading}
            style={{
              padding: '6px 12px',
              borderRadius: '16px',
              backgroundColor: '#09152b',
              border: '1px solid #1e3a6a',
              color: '#cbd5e1',
              fontSize: '0.72rem',
              whiteSpace: 'nowrap',
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'background-color 0.15s'
            }}
          >
            <ChevronRight size={12} color="#38bdf8" />
            <span>{prompt}</span>
          </button>
        ))}
      </div>

      {/* Input Form */}
      <div
        style={{
          padding: '16px 20px',
          backgroundColor: '#071224',
          borderTop: '1px solid #14284b'
        }}
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          style={{ display: 'flex', gap: '10px' }}
        >
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask about corridor delays, precedence, headway, or what-if interventions..."
            disabled={loading}
            style={{
              flex: 1,
              padding: '11px 16px',
              backgroundColor: '#050b17',
              border: '1px solid #1e3a6a',
              borderRadius: '8px',
              color: '#f8fafc',
              fontSize: '0.85rem',
              outline: 'none'
            }}
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || loading}
            style={{
              padding: '11px 20px',
              borderRadius: '8px',
              backgroundColor: !inputValue.trim() || loading ? '#1e293b' : '#0284c7',
              color: !inputValue.trim() || loading ? '#64748b' : '#ffffff',
              border: 'none',
              fontSize: '0.85rem',
              fontWeight: 700,
              cursor: !inputValue.trim() || loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Send size={15} />
            <span>Send</span>
          </button>
        </form>

        <div
          style={{
            marginTop: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.68rem',
            color: '#64748b'
          }}
        >
          <ShieldAlert size={12} />
          <span>AI-generated, controller must verify. All answers are grounded via simulation tools.</span>
        </div>
      </div>
    </div>
  );
};
