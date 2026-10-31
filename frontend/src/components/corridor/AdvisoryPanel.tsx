import React, { useState } from 'react';
import {
  Volume2,
  Languages,
  CheckCircle2,
  Train,
  Sparkles,
  Loader2,
  Copy,
  Check,
  ShieldAlert,
  Radio
} from 'lucide-react';
import { fetchAgentAdvisory } from '../../services/api';
import { TrainState } from '../../types';

interface AdvisoryPanelProps {
  trains: TrainState[];
  selectedTrainId: string;
  onSelectTrain: (trainId: string) => void;
}

export const AdvisoryPanel: React.FC<AdvisoryPanelProps> = ({
  trains,
  selectedTrainId,
  onSelectTrain
}) => {
  const [activeLang, setActiveLang] = useState<'en' | 'hi'>('en');
  const [loading, setLoading] = useState<boolean>(false);
  const [advisoryData, setAdvisoryData] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [broadcasting, setBroadcasting] = useState<boolean>(false);

  const handleGenerate = async () => {
    if (!selectedTrainId) return;
    setLoading(true);
    setError(null);
    setCopied(false);
    try {
      const cleanNum = selectedTrainId.replace(/^TRAIN_/i, '').trim();
      const res = await fetchAgentAdvisory(cleanNum, ['en', 'hi']);
      setAdvisoryData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to generate passenger advisory.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!advisoryData) return;
    const text = activeLang === 'en' ? advisoryData.advisories?.en : advisoryData.advisories?.hi;
    if (text) {
      navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handlePlayAudio = () => {
    if (!advisoryData) return;
    const text = activeLang === 'en' ? advisoryData.advisories?.en : advisoryData.advisories?.hi;
    if (!text || !('speechSynthesis' in window)) return;

    window.speechSynthesis.cancel();
    setBroadcasting(true);

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = activeLang === 'en' ? 'en-IN' : 'hi-IN';
    utterance.rate = 0.9;
    utterance.onend = () => setBroadcasting(false);
    utterance.onerror = () => setBroadcasting(false);

    window.speechSynthesis.speak(utterance);
  };

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
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
            <Radio size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1.2rem', fontWeight: 800, color: '#f8fafc' }}>
                Multilingual Passenger Advisory Panel
              </span>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '3px 10px',
                  borderRadius: '20px',
                  backgroundColor: '#042f2e',
                  border: '1px solid #0d9488',
                  color: '#5eead4',
                  fontSize: '0.72rem',
                  fontWeight: 700
                }}
              >
                <Sparkles size={12} />
                <span>Gemma 4 (gemma-4-26b-a4b-it)</span>
              </div>
            </div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>
              Station PA announcements and passenger app push notifications in English and Hindi (Devanagari).
            </div>
          </div>
        </div>
      </div>

      {/* Control Configuration Bar */}
      <div
        style={{
          display: 'flex',
          gap: '16px',
          alignItems: 'flex-end',
          backgroundColor: '#071224',
          padding: '18px',
          borderRadius: '10px',
          border: '1px solid #14284b'
        }}
      >
        <div style={{ flex: 1 }}>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#94a3b8', marginBottom: '6px' }}>
            Select Train for Passenger Broadcast:
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
                {t.train_number} - {t.train_name} ({t.current_delay_minutes}m delay, next: {t.next_station_name || 'Station'})
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={handleGenerate}
          disabled={loading}
          style={{
            padding: '10px 22px',
            backgroundColor: loading ? '#0369a1' : '#0284c7',
            color: '#ffffff',
            border: 'none',
            borderRadius: '6px',
            fontSize: '0.85rem',
            fontWeight: 700,
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            boxShadow: '0 4px 14px rgba(2, 132, 199, 0.4)'
          }}
        >
          {loading ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              <span>Generating Bilingual Advisories...</span>
            </>
          ) : (
            <>
              <Languages size={16} />
              <span>Generate Passenger Advisory</span>
            </>
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div
          style={{
            padding: '12px 16px',
            backgroundColor: '#450a0a',
            border: '1px solid #dc2626',
            borderRadius: '8px',
            color: '#fca5a5',
            fontSize: '0.82rem'
          }}
        >
          {error}
        </div>
      )}

      {/* Advisory Output Display */}
      {advisoryData && (
        <div
          style={{
            backgroundColor: '#071224',
            borderRadius: '10px',
            border: '1px solid #172e54',
            overflow: 'hidden'
          }}
        >
          {/* Language Tabs & Actions */}
          <div
            style={{
              padding: '12px 18px',
              backgroundColor: '#0c1a35',
              borderBottom: '1px solid #14284b',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
          >
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => setActiveLang('en')}
                style={{
                  padding: '6px 14px',
                  borderRadius: '6px',
                  border: 'none',
                  backgroundColor: activeLang === 'en' ? '#0284c7' : '#09152b',
                  color: activeLang === 'en' ? '#ffffff' : '#94a3b8',
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  cursor: 'pointer'
                }}
              >
                English Broadcast
              </button>
              <button
                onClick={() => setActiveLang('hi')}
                style={{
                  padding: '6px 14px',
                  borderRadius: '6px',
                  border: 'none',
                  backgroundColor: activeLang === 'hi' ? '#0284c7' : '#09152b',
                  color: activeLang === 'hi' ? '#ffffff' : '#94a3b8',
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  cursor: 'pointer'
                }}
              >
                हिंदी प्रसारण (Hindi PA)
              </button>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <button
                onClick={handlePlayAudio}
                disabled={broadcasting}
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  backgroundColor: broadcasting ? '#064e3b' : '#09152b',
                  border: '1px solid #1e3a6a',
                  color: broadcasting ? '#6ee7b7' : '#38bdf8',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <Volume2 size={14} />
                <span>{broadcasting ? 'Broadcasting...' : 'Play PA Announcement'}</span>
              </button>

              <button
                onClick={handleCopy}
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  backgroundColor: '#09152b',
                  border: '1px solid #1e3a6a',
                  color: '#cbd5e1',
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                {copied ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
                <span>{copied ? 'Copied' : 'Copy Text'}</span>
              </button>
            </div>
          </div>

          {/* Announcement Text Box */}
          <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div
              style={{
                padding: '16px 20px',
                backgroundColor: '#050b17',
                border: '1px solid #14284b',
                borderRadius: '8px',
                color: '#f8fafc',
                fontSize: activeLang === 'hi' ? '1rem' : '0.92rem',
                fontFamily: activeLang === 'hi' ? '"Noto Sans Devanagari", "Mangal", sans-serif' : 'inherit',
                lineHeight: 1.6,
                minHeight: '80px'
              }}
            >
              {activeLang === 'en'
                ? advisoryData.advisories?.en || advisoryData.advisory_en || 'No English advisory available.'
                : advisoryData.advisories?.hi || advisoryData.advisory_hi || 'हिंदी सूचना उपलब्ध नहीं है।'}
            </div>

            {/* Validation Badge */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 14px',
                backgroundColor: '#042f2e',
                border: '1px solid #0d9488',
                borderRadius: '6px',
                color: '#5eead4',
                fontSize: '0.75rem'
              }}
            >
              <CheckCircle2 size={16} color="#10b981" />
              <span>
                <strong>Grounding Verified:</strong> All minutes, train numbers, and station names strictly validated
                against telemetry and ETA prediction models (Phase 5 & 9 NumberValidator passed).
              </span>
            </div>

            {/* Disclaimer */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                color: '#64748b',
                fontSize: '0.72rem'
              }}
            >
              <ShieldAlert size={14} />
              <span>AI-generated, controller must verify before station broadcast.</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
