import React, { useEffect, useState } from 'react';
import { RefreshCw, Bell, Share2, Edit3, Grid, Check, Info, Calendar } from 'lucide-react';

import { TrainState, TrainRouteResponse, StationRouteItem } from '../types';
import { fetchTrainRoute } from '../services/api';
import { DelayReasonModal } from './DelayReasonModal';
import { CoachLayoutModal } from './CoachLayoutModal';

interface WhereIsMyTrainViewProps {
  trains: TrainState[];
  selectedTrainId: string;
  onSelectTrain: (trainId: string) => void;
}

export const WhereIsMyTrainView: React.FC<WhereIsMyTrainViewProps> = ({
  trains,
  selectedTrainId,
  onSelectTrain
}) => {
  const [routeData, setRouteData] = useState<TrainRouteResponse | null>(null);
  const [selectedStation, setSelectedStation] = useState<StationRouteItem | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedDay, setSelectedDay] = useState<'Yesterday' | 'Today' | 'Tomorrow'>('Today');

  const todayISO = new Date().toISOString().split('T')[0];
  const [selectedDate, setSelectedDate] = useState<string>(todayISO);

  // Modals & Notifications
  const [isCoachModalOpen, setIsCoachModalOpen] = useState<boolean>(false);
  const [isAlarmModalOpen, setIsAlarmModalOpen] = useState<boolean>(false);
  const [alarmStation, setAlarmStation] = useState<string>('');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const loadRoute = (tId: string, isInitial: boolean = false, dateToUse?: string) => {
    const d = dateToUse !== undefined ? dateToUse : selectedDate;
    if (isInitial || !routeData || routeData.train_id !== tId) {
      setLoading(true);
    }
    fetchTrainRoute(tId, d)
      .then((data) => {
        setRouteData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching train route:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadRoute(selectedTrainId, true, selectedDate);
    const interval = setInterval(() => loadRoute(selectedTrainId, false, selectedDate), 3000);
    return () => clearInterval(interval);
  }, [selectedTrainId, selectedDate]);

  const activeTrain = trains.find((t) => t.train_id === selectedTrainId) || trains[0];
  const isDelayed = routeData ? routeData.total_delay_minutes > 5 : false;

  const handleShare = () => {
    const text = `🚆 ${activeTrain?.train_number} ${activeTrain?.train_name}\nStatus: ${routeData?.status_message || 'Running'}\nLive Delay: ${Math.round(routeData?.total_delay_minutes || 0)} mins\nDate: ${selectedDate}\nCheck live updates on SIH Dynamic ETA Forecast App!`;
    navigator.clipboard?.writeText(text);
    showToast('📋 Live status copied to clipboard!');
  };

  const handleQuickDate = (type: 'yesterday' | 'today' | 'tomorrow') => {
    const d = new Date();
    if (type === 'yesterday') d.setDate(d.getDate() - 1);
    if (type === 'tomorrow') d.setDate(d.getDate() + 1);
    const iso = d.toISOString().split('T')[0];
    setSelectedDate(iso);
  };


  const handleSetAlarm = () => {
    if (!alarmStation) {
      showToast('⚠️ Please select a destination station for alarm!');
      return;
    }
    setIsAlarmModalOpen(false);
    showToast(`🔔 Destination wake-up alarm set for ${alarmStation}!`);
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      backgroundColor: '#0c1017',
      color: '#f8fafc',
      fontFamily: 'Inter, sans-serif',
      position: 'relative',
      overflow: 'hidden'
    }}>
      
      {/* Toast Notification */}
      {toastMessage && (
        <div style={{
          position: 'absolute',
          top: '20px',
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'rgba(2, 132, 199, 0.95)',
          color: 'white',
          padding: '10px 20px',
          borderRadius: '24px',
          fontSize: '0.85rem',
          fontWeight: 700,
          zIndex: 3000,
          boxShadow: '0 10px 30px rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <Info size={16} />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* 1. Header Toolbar (Where is My Train Style) */}
      <div style={{
        background: '#121824',
        padding: '12px 20px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px'
      }}>
        
        {/* Top Row: Train Selection Dropdown */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px' }}>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1 }}>
            <div style={{
              background: '#0284c7',
              color: 'white',
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              fontSize: '1.1rem'
            }}>
              🚆
            </div>

            <div style={{ flex: 1 }}>
              <select
                value={selectedTrainId}
                onChange={(e) => onSelectTrain(e.target.value)}
                style={{
                  background: 'rgba(15, 23, 42, 0.9)',
                  border: '1px solid rgba(56, 189, 248, 0.4)',
                  color: '#f8fafc',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  fontSize: '0.95rem',
                  fontWeight: 700,
                  width: '100%',
                  cursor: 'pointer'
                }}
              >
                {trains.map((t) => (
                  <option key={t.train_id} value={t.train_id}>
                    {t.train_number} {t.train_name} ({t.origin_station_name} ➔ {t.destination_station_name})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Quick Action Badges */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              className="glass-button"
              onClick={() => setIsCoachModalOpen(true)}
              style={{ padding: '6px 12px', fontSize: '0.75rem', borderRadius: '20px' }}
            >
              <Grid size={13} color="#a855f7" />
              <span>Coach</span>
            </button>

            <button
              className="glass-button"
              onClick={() => setIsAlarmModalOpen(true)}
              style={{ padding: '6px 12px', fontSize: '0.75rem', borderRadius: '20px' }}
            >
              <Bell size={13} color="#38bdf8" />
              <span>Alarm</span>
            </button>

            <button
              className="glass-button"
              onClick={handleShare}
              style={{ padding: '6px 12px', fontSize: '0.75rem', borderRadius: '20px' }}
            >
              <Share2 size={13} color="#94a3b8" />
              <span>Share</span>
            </button>
          </div>

        </div>

        {/* Full Interactive Date Calendar Picker & Quick Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={() => handleQuickDate('yesterday')}
              style={{
                background: 'rgba(30, 41, 59, 0.6)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#94a3b8',
                padding: '4px 12px',
                borderRadius: '16px',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              ⏪ Yesterday
            </button>

            <button
              onClick={() => handleQuickDate('today')}
              style={{
                background: selectedDate === todayISO ? 'rgba(56, 189, 248, 0.25)' : 'rgba(30, 41, 59, 0.6)',
                border: selectedDate === todayISO ? '1px solid #38bdf8' : '1px solid rgba(255, 255, 255, 0.1)',
                color: selectedDate === todayISO ? '#38bdf8' : '#94a3b8',
                padding: '4px 12px',
                borderRadius: '16px',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer'
              }}
            >
              📅 Today
            </button>

            <button
              onClick={() => handleQuickDate('tomorrow')}
              style={{
                background: 'rgba(30, 41, 59, 0.6)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#94a3b8',
                padding: '4px 12px',
                borderRadius: '16px',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              ⏩ Tomorrow
            </button>
          </div>

          {/* Full Interactive Date Calendar Input */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(15, 23, 42, 0.9)', padding: '4px 10px', borderRadius: '12px', border: '1px solid rgba(56, 189, 248, 0.3)' }}>
            <Calendar size={14} color="#38bdf8" />
            <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600 }}>Calendar Date:</span>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => {
                if (e.target.value) {
                  setSelectedDate(e.target.value);
                  showToast(`📅 Loaded live/historical timeline for ${e.target.value}`);
                }
              }}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#38bdf8',
                fontFamily: 'monospace',
                fontSize: '0.8rem',
                fontWeight: 700,
                outline: 'none',
                cursor: 'pointer'
              }}
            />
          </div>

        </div>


      </div>

      {/* 2. Route Table Column Headers */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '90px 1fr 90px',
        padding: '8px 24px',
        background: '#0a0e17',
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        fontSize: '0.75rem',
        fontWeight: 700,
        color: '#64748b',
        textTransform: 'uppercase',
        letterSpacing: '0.5px'
      }}>
        <div>Arrival</div>
        <div style={{ paddingLeft: '40px' }}>Station & Platform</div>
        <div style={{ textAlign: 'right' }}>Departure</div>
      </div>

      {/* 3. Vertical Station Route Timeline Scroll Container */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px 24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '0px'
      }}>
        {loading && !routeData ? (
          <div style={{ padding: '60px', textAlign: 'center', color: '#94a3b8' }}>
            Fetching dynamic train schedule...
          </div>
        ) : routeData ? (
          routeData.route_items.map((st, idx) => {
            const isStationDelayed = st.arrival_delay_minutes > 0;
            const isPassed = st.status === 'PASSED';
            const isCurrent = st.is_current_position;

            return (
              <div
                key={st.station_id}
                onClick={() => setSelectedStation(st)}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '90px 1fr 90px',
                  alignItems: 'center',
                  padding: '14px 0',
                  position: 'relative',
                  cursor: 'pointer',
                  borderRadius: '8px',
                  transition: 'background 0.15s ease'
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
              >
                
                {/* Left Column: Scheduled & Actual/Forecasted Arrival */}
                <div style={{ display: 'flex', flexDirection: 'column', fontSize: '0.85rem' }}>
                  <span style={{ color: isPassed ? '#64748b' : '#94a3b8', fontSize: '0.78rem' }}>
                    {st.scheduled_arrival}
                  </span>
                  <span style={{
                    fontWeight: 700,
                    fontSize: '0.9rem',
                    color: isPassed
                      ? '#64748b'
                      : isStationDelayed
                      ? '#ef4444'
                      : '#34d399'
                  }}>
                    {st.forecasted_arrival}
                  </span>
                </div>

                {/* Center Column: Vertical Line + Dot/Train + Station Info */}
                <div style={{ display: 'flex', alignItems: 'center', position: 'relative', height: '100%' }}>
                  
                  {/* Vertical Rail Line */}
                  {idx < routeData.route_items.length - 1 && (
                    <div style={{
                      position: 'absolute',
                      left: '12px',
                      top: '20px',
                      bottom: '-24px',
                      width: '4px',
                      background: isPassed ? '#334155' : '#38bdf8',
                      zIndex: 1,
                      borderRadius: '2px'
                    }} />
                  )}

                  {/* Node Dot / Current Train Badge */}
                  <div style={{ position: 'relative', zIndex: 2, marginRight: '16px' }}>
                    {isCurrent || (st as any).is_in_between ? (
                      <div style={{
                        background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
                        color: 'white',
                        padding: '6px 12px',
                        borderRadius: '20px',
                        fontSize: '0.8rem',
                        fontWeight: 800,
                        boxShadow: '0 0 20px rgba(56, 189, 248, 0.8)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        border: '2px solid #38bdf8',
                        animation: 'pulse 2s infinite'
                      }}>
                        <span style={{ fontSize: '1rem' }}>🚆</span>
                        <span>LIVE POINTER: {(st as any).speed_kmh || activeTrain?.speed_kmh || 110} km/h</span>
                      </div>
                    ) : (
                      <div style={{
                        width: '12px',
                        height: '12px',
                        borderRadius: '50%',
                        background: isPassed ? '#475569' : '#38bdf8',
                        border: '2px solid #0c1017',
                        boxShadow: isPassed ? 'none' : '0 0 8px #38bdf8'
                      }} />
                    )}
                  </div>

                  {/* Station Name & Platform Pill */}
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{
                        fontSize: (st as any).is_in_between ? '1.05rem' : '1rem',
                        fontWeight: (st as any).is_in_between ? 800 : 700,
                        color: (st as any).is_in_between ? '#38bdf8' : (isPassed ? '#94a3b8' : '#f8fafc'),
                        fontFamily: 'Outfit, sans-serif'
                      }}>
                        {st.station_name}
                      </span>
                      {((st as any).is_in_between || isCurrent) && (
                        <span style={{
                          background: 'rgba(234, 179, 8, 0.25)',
                          border: '1px solid #eab308',
                          color: '#fef08a',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontSize: '0.72rem',
                          fontWeight: 800
                        }}>
                          📍 CURRENT LOCATION (EN ROUTE BETWEEN STATIONS)
                        </span>
                      )}
                    </div>



                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                        {st.distance_km} km
                      </span>

                      {/* Platform Badge */}
                      <span style={{
                        background: 'rgba(30, 41, 59, 0.8)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        color: '#cbd5e1',
                        padding: '1px 8px',
                        borderRadius: '12px',
                        fontSize: '0.72rem',
                        fontWeight: 600,
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}>
                        <span>{st.platform_number}</span>
                        <Edit3 size={10} color="#64748b" />
                      </span>

                      {/* Live Telemetry Delay Badge */}
                      <span style={{
                        background: (st.live_telemetry_delay_minutes || 0) > 15 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                        border: (st.live_telemetry_delay_minutes || 0) > 15 ? '1px solid #ef4444' : '1px solid #10b981',
                        color: (st.live_telemetry_delay_minutes || 0) > 15 ? '#fca5a5' : '#6ee7b7',
                        padding: '1px 8px',
                        borderRadius: '12px',
                        fontSize: '0.7rem',
                        fontWeight: 700
                      }}>
                        📡 Live: {st.live_telemetry_delay_minutes ? `+${st.live_telemetry_delay_minutes}m` : 'On Time'}
                      </span>

                      {/* ML Forecasted Delay Badge */}
                      {st.ml_predicted_delay_minutes !== undefined && (
                        <span style={{
                          background: 'rgba(168, 85, 247, 0.2)',
                          border: '1px solid #a855f7',
                          color: '#e9d5ff',
                          padding: '1px 8px',
                          borderRadius: '12px',
                          fontSize: '0.7rem',
                          fontWeight: 700
                        }}>
                          🧠 ML Est: +{st.ml_predicted_delay_minutes}m ({st.ml_forecasted_arrival})
                        </span>
                      )}

                      {/* Probabilistic Quantile Fan-Chart Uncertainty Band Badge */}
                      {st.eta_p10 && st.eta_p90 && (
                        <span style={{
                          background: 'linear-gradient(90deg, rgba(2, 132, 199, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%)',
                          border: '1px solid rgba(56, 189, 248, 0.4)',
                          color: '#38bdf8',
                          padding: '1px 10px',
                          borderRadius: '12px',
                          fontSize: '0.7rem',
                          fontWeight: 700,
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}>
                          <span>📊 Fan-Chart [P10..P90]:</span>
                          <span style={{ color: '#6ee7b7' }}>{st.eta_p10}</span>
                          <span>–</span>
                          <span style={{ color: '#fca5a5' }}>{st.eta_p90}</span>
                          <span style={{ color: '#cbd5e1', fontSize: '0.65rem' }}>(±{st.confidence_margin_minutes || 4}m)</span>
                        </span>
                      )}
                    </div>

                  </div>

                </div>

                {/* Right Column: Scheduled & Actual/Forecasted Departure */}
                <div style={{ display: 'flex', flexDirection: 'column', textAlign: 'right', fontSize: '0.85rem' }}>
                  <span style={{ color: isPassed ? '#64748b' : '#94a3b8', fontSize: '0.78rem' }}>
                    {st.scheduled_departure}
                  </span>
                  <span style={{
                    fontWeight: 700,
                    fontSize: '0.9rem',
                    color: isPassed
                      ? '#64748b'
                      : isStationDelayed
                      ? '#ef4444'
                      : '#34d399'
                  }}>
                    {st.forecasted_departure}
                  </span>
                </div>

              </div>
            );
          })
        ) : null}
      </div>

      {/* 4. Bottom Fixed Live Status Bar (Where is My Train Style) */}
      {routeData && (
        <div style={{
          background: '#121824',
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          padding: '14px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          zIndex: 500,
          boxShadow: '0 -8px 24px rgba(0,0,0,0.5)'
        }}>
          <div>
            <h2 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.15rem', fontWeight: 800, color: '#f8fafc' }}>
              {routeData.status_message}
            </h2>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '4px' }}>
              <span style={{
                background: isDelayed ? 'rgba(239, 68, 68, 0.18)' : 'rgba(16, 185, 129, 0.18)',
                border: isDelayed ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid rgba(16, 185, 129, 0.4)',
                color: isDelayed ? '#f87171' : '#34d399',
                padding: '3px 10px',
                borderRadius: '16px',
                fontSize: '0.75rem',
                fontWeight: 700,
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px'
              }}>
                <span className={`pulse-dot ${isDelayed ? 'pulse-dot-red' : 'pulse-dot-green'}`}></span>
                <span>{isDelayed ? `Delayed by ${Math.round(routeData.total_delay_minutes)} mins` : 'Running On Time'}</span>
              </span>

              {routeData.formatted_confidence_eta && (
                <span style={{
                  background: 'rgba(56, 189, 248, 0.15)',
                  border: '1px solid rgba(56, 189, 248, 0.3)',
                  color: '#38bdf8',
                  padding: '3px 10px',
                  borderRadius: '16px',
                  fontSize: '0.75rem',
                  fontWeight: 700
                }}>
                  🎯 ML Forecast: {routeData.formatted_confidence_eta}
                </span>
              )}

              <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
                Updated {routeData.last_updated}
              </span>
            </div>
          </div>


          <button
            className="glass-button"
            onClick={() => loadRoute(selectedTrainId)}
            style={{ padding: '10px', borderRadius: '50%' }}
            title="Refresh Live Status"
          >
            <RefreshCw size={18} color="#38bdf8" />
          </button>
        </div>
      )}

      {/* Clickable Delay Reasons Modal */}
      <DelayReasonModal
        station={selectedStation}
        onClose={() => setSelectedStation(null)}
      />

      {/* Rake Coach Position Modal */}
      {isCoachModalOpen && (
        <CoachLayoutModal
          train={activeTrain}
          onClose={() => setIsCoachModalOpen(false)}
        />
      )}

      {/* Alarm Configuration Modal */}
      {isAlarmModalOpen && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(2, 6, 23, 0.85)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2000
        }}>
          <div className="glass-panel" style={{ width: '380px', padding: '24px', borderRadius: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <Bell size={20} color="#38bdf8" />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800 }}>Destination Wake-up Alarm</h3>
            </div>
            
            <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '14px' }}>
              Receive loud alarm 15 minutes before reaching your chosen station:
            </p>

            <select
              value={alarmStation}
              onChange={(e) => setAlarmStation(e.target.value)}
              style={{
                width: '100%',
                background: 'rgba(15, 23, 42, 0.9)',
                border: '1px solid rgba(56, 189, 248, 0.4)',
                color: 'white',
                padding: '10px',
                borderRadius: '8px',
                marginBottom: '20px',
                fontSize: '0.85rem'
              }}
            >
              <option value="">-- Select Destination Station --</option>
              {routeData?.route_items.map((st) => (
                <option key={st.station_id} value={st.station_name}>
                  {st.station_name} ({st.scheduled_arrival})
                </option>
              ))}
            </select>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button className="glass-button" onClick={() => setIsAlarmModalOpen(false)}>Cancel</button>
              <button className="glass-button glass-button-primary" onClick={handleSetAlarm}>Set Alarm</button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
