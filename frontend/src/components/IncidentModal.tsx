import React, { useState } from 'react';
import { X, AlertTriangle, CloudFog, CloudRain, Flame, ShieldAlert, CheckCircle } from 'lucide-react';
import { injectIncident, clearAllIncidents } from '../services/api';

interface IncidentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onIncidentInjected?: () => void;
}

export const IncidentModal: React.FC<IncidentModalProps> = ({ isOpen, onClose, onIncidentInjected }) => {
  const [selectedSection, setSelectedSection] = useState<string>('MTJ-AGC');
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const sections = [
    { id: 'NDLS-MTJ', label: 'NDLS - MTJ (New Delhi ➔ Mathura)' },
    { id: 'MTJ-AGC', label: 'MTJ - AGC (Mathura ➔ Agra Cantt)' },
    { id: 'AGC-GWL', label: 'AGC - GWL (Agra Cantt ➔ Gwalior)' },
    { id: 'GWL-VGLJ', label: 'GWL - VGLJ (Gwalior ➔ Jhansi)' },
    { id: 'VGLJ-BINA', label: 'VGLJ - BINA (Jhansi ➔ Bina)' },
    { id: 'BINA-BPL', label: 'BINA - BPL (Bina ➔ Bhopal)' },
    { id: 'BPL-NGP', label: 'BPL - NGP (Bhopal ➔ Nagpur)' },
    { id: 'NGP-BPQ', label: 'NGP - BPQ (Nagpur ➔ Balharshah)' },
    { id: 'BPQ-BZA', label: 'BPQ - BZA (Balharshah ➔ Vijayawada)' },
    { id: 'BZA-MAS', label: 'BZA - MAS (Vijayawada ➔ Chennai Central)' },
    { id: 'NDLS-CNB', label: 'NDLS - CNB (New Delhi ➔ Kanpur Central)' },
    { id: 'CNB-PRYJ', label: 'CNB - PRYJ (Kanpur ➔ Prayagraj)' },
    { id: 'PRYJ-DDU', label: 'PRYJ - DDU (Prayagraj ➔ Pt. Deen Dayal Upadhyaya)' },
    { id: 'DDU-DHN', label: 'DDU - DHN (Pt. Deen Dayal Upadhyaya ➔ Dhanbad)' },
    { id: 'DHN-HWH', label: 'DHN - HWH (Dhanbad ➔ Howrah Junction)' },
    { id: 'DEC-JP', label: 'DEC - JP (Delhi Cantt ➔ Jaipur)' },
    { id: 'JP-AII', label: 'JP - AII (Jaipur ➔ Ajmer)' },
    { id: 'PNP-UMB', label: 'PNP - UMB (Panipat ➔ Ambala Cantt)' },
    { id: 'UMB-LDH', label: 'UMB - LDH (Ambala ➔ Ludhiana)' },
    { id: 'KIR-GHY', label: 'KIR - GHY (Katihar ➔ Guwahati)' }
  ];

  const handleInject = async (eventType: string, severity: string = 'HIGH', visibility: number = 150) => {
    try {
      await injectIncident({
        event_type: eventType,
        section_id: selectedSection,
        severity,
        visibility_meters: visibility
      });
      setStatusMessage(`Successfully injected ${eventType} on section ${selectedSection}!`);
      setTimeout(() => setStatusMessage(null), 3000);
      if (onIncidentInjected) onIncidentInjected();
    } catch (err) {
      console.error('Error injecting incident:', err);
    }
  };

  const handleClearAll = async () => {
    try {
      await clearAllIncidents();
      setStatusMessage('All injected incidents cleared!');
      setTimeout(() => setStatusMessage(null), 3000);
      if (onIncidentInjected) onIncidentInjected();
    } catch (err) {
      console.error('Error clearing incidents:', err);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999
    }}>
      <div className="glass-panel" style={{ width: '500px', padding: '24px', position: 'relative' }}>
        
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AlertTriangle color="#ef4444" size={22} />
            <h2 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.15rem', fontWeight: 700 }}>
              Inject Operational Incident
            </h2>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {statusMessage && (
          <div style={{
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.4)',
            color: '#34d399',
            padding: '8px 12px',
            borderRadius: '6px',
            fontSize: '0.8rem',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <CheckCircle size={16} />
            <span>{statusMessage}</span>
          </div>
        )}

        {/* Target Train Selector */}
        <div style={{ marginBottom: '14px' }}>
          <label style={{ display: 'block', fontSize: '0.78rem', color: '#94a3b8', marginBottom: '6px', fontWeight: 600 }}>
            TARGET TRAIN (MATCHES PASSENGER VIEW):
          </label>
          <select
            onChange={(e) => {
              const trainSectionMap: Record<string, string> = {
                'TRAIN_12951': 'NDLS-MTJ',
                'TRAIN_12302': 'NDLS-CNB',
                'TRAIN_12626': 'BPL-NGP',
                'TRAIN_12002': 'MTJ-AGC',
                'TRAIN_12424': 'CNB-PRYJ',
                'TRAIN_12958': 'DEC-JP',
                'TRAIN_12425': 'PNP-UMB',
                'TRAIN_12622': 'NGP-BPQ',
                'TRAIN_12724': 'KZJ-SC',
                'TRAIN_12260': 'DDU-DHN'
              };
              if (trainSectionMap[e.target.value]) {
                setSelectedSection(trainSectionMap[e.target.value]);
              }
            }}
            style={{
              width: '100%',
              background: 'rgba(15, 23, 42, 0.9)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              color: '#38bdf8',
              padding: '10px',
              borderRadius: '8px',
              fontSize: '0.85rem',
              fontWeight: 600
            }}
          >
            <option value="TRAIN_12951">12951 Mumbai Rajdhani Express</option>
            <option value="TRAIN_12302">12302 Howrah Rajdhani Express</option>
            <option value="TRAIN_12626">12626 Kerala Express</option>
            <option value="TRAIN_12002">12002 Rani Kamlapati Shatabdi</option>
            <option value="TRAIN_12424">12424 Dibrugarh Rajdhani Express</option>
            <option value="TRAIN_12958">12958 Swarna Jayanti Rajdhani</option>
            <option value="TRAIN_12425">12425 Jammu Rajdhani Express</option>
            <option value="TRAIN_12622">12622 Tamil Nadu Express</option>
            <option value="TRAIN_12724">12724 Telangana Express</option>
            <option value="TRAIN_12260">12260 Sealdah Duronto Express</option>
          </select>
        </div>

        {/* Section Selector */}
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontSize: '0.78rem', color: '#94a3b8', marginBottom: '6px' }}>
            SELECT TARGET RAILWAY SECTION:
          </label>
          <select
            value={selectedSection}
            onChange={(e) => setSelectedSection(e.target.value)}
            style={{
              width: '100%',
              background: 'rgba(15, 23, 42, 0.9)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              color: '#f8fafc',
              padding: '10px',
              borderRadius: '8px',
              fontSize: '0.85rem'
            }}
          >
            {sections.map((sec) => (
              <option key={sec.id} value={sec.id}>{sec.label}</option>
            ))}
          </select>
        </div>

        {/* Incident Trigger Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '20px' }}>
          <button className="glass-button" onClick={() => handleInject('CHAIN_PULLING', 'CRITICAL')} style={{ justifyContent: 'center', background: 'rgba(239, 68, 68, 0.18)', border: '1px solid #ef4444', gridColumn: 'span 2' }}>
            <AlertTriangle size={16} color="#ef4444" />
            <span style={{ fontWeight: 800, color: '#fca5a5' }}>🚨 Alarm Chain Pulling (ACP) (6-8m Station / 10-15m Mid-Route)</span>
          </button>

          <button className="glass-button" onClick={() => handleInject('FOG', 'HIGH', 150)} style={{ justifyContent: 'center' }}>
            <CloudFog size={16} color="#f59e0b" />
            <span>Dense Fog (Visibility 150m)</span>
          </button>

          <button className="glass-button" onClick={() => handleInject('HEAVY_RAIN', 'MEDIUM', 800)} style={{ justifyContent: 'center' }}>
            <CloudRain size={16} color="#38bdf8" />
            <span>Heavy Rain Storm</span>
          </button>

          <button className="glass-button" onClick={() => handleInject('SIGNAL_FAILURE', 'CRITICAL')} style={{ justifyContent: 'center' }}>
            <Flame size={16} color="#ef4444" />
            <span>Signal Interlocking Failure</span>
          </button>

          <button className="glass-button" onClick={() => handleInject('JUNCTION_CONGESTION', 'HIGH')} style={{ justifyContent: 'center' }}>
            <ShieldAlert size={16} color="#a855f7" />
            <span>Junction Route Conflict</span>
          </button>

          <button className="glass-button" onClick={() => handleInject('PLATFORM_OCCUPIED', 'MEDIUM')} style={{ justifyContent: 'center' }}>
            <AlertTriangle size={16} color="#fbbf24" />
            <span>Platform Occupancy Hold (+12m)</span>
          </button>

          <button className="glass-button" onClick={() => handleInject('MAINTENANCE_BLOCK', 'CRITICAL')} style={{ justifyContent: 'center' }}>
            <AlertTriangle size={16} color="#dc2626" />
            <span>Track Maintenance Block (+25m)</span>
          </button>
        </div>


        <button
          className="glass-button glass-button-danger"
          onClick={handleClearAll}
          style={{ width: '100%', justifyContent: 'center', padding: '10px' }}
        >
          <span>Clear All Injected Incidents</span>
        </button>

      </div>
    </div>
  );
};
