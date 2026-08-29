import React, { useState } from 'react';
import { PlayCircle, CheckCircle2, ChevronRight, Award } from 'lucide-react';
import { triggerSIHDemoStep } from '../services/api';

interface DemoScenarioBarProps {
  onStepTriggered?: () => void;
}

export const DemoScenarioBar: React.FC<DemoScenarioBarProps> = ({ onStepTriggered }) => {
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [stepDescription, setStepDescription] = useState<string>(
    'Click "Step 1: Baseline ETA" to launch the predefined SIH26028 dynamic simulation.'
  );

  const steps = [
    { num: 1, label: '1. Baseline Schedule (22:41)' },
    { num: 2, label: '2. Signal Halt (+10m)' },
    { num: 3, label: '3. Fog Zone (+9m)' },
    { num: 4, label: '4. Junction Precedence (+7m)' },
    { num: 5, label: '5. Clearance & Recovery (-5m)' }
  ];

  const handleNextStep = async () => {
    try {
      const res = await triggerSIHDemoStep();
      setCurrentStep(res.demo_step);
      setStepDescription(res.description);
      if (onStepTriggered) onStepTriggered();
    } catch (err) {
      console.error('Error triggering demo step:', err);
    }
  };

  return (
    <div className="glass-panel-glow" style={{ padding: '12px 20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
      
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Award size={18} color="#38bdf8" />
          <span style={{ fontFamily: 'Outfit, sans-serif', fontWeight: 700, fontSize: '0.9rem', color: '#f8fafc' }}>
            SIH 2026 JUDGES DEMONSTRATION SCENARIO (Train 12951 NDLS-BPL Rajdhani)
          </span>
        </div>

        <button className="glass-button glass-button-primary" onClick={handleNextStep} style={{ padding: '6px 14px', fontSize: '0.8rem' }}>
          <PlayCircle size={15} />
          <span>Execute Step {currentStep === 0 || currentStep === 5 ? 1 : currentStep + 1}</span>
          <ChevronRight size={14} />
        </button>
      </div>

      {/* Step Indicators */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {steps.map((st) => {
          const isActive = currentStep === st.num;
          const isPassed = currentStep > st.num;
          return (
            <div
              key={st.num}
              style={{
                flex: 1,
                padding: '6px 10px',
                borderRadius: '6px',
                fontSize: '0.75rem',
                fontWeight: 600,
                textAlign: 'center',
                background: isActive
                  ? 'rgba(56, 189, 248, 0.25)'
                  : isPassed
                  ? 'rgba(16, 185, 129, 0.15)'
                  : 'rgba(30, 41, 59, 0.5)',
                border: isActive
                  ? '1px solid #38bdf8'
                  : isPassed
                  ? '1px solid rgba(16, 185, 129, 0.4)'
                  : '1px solid rgba(255, 255, 255, 0.08)',
                color: isActive ? '#38bdf8' : isPassed ? '#34d399' : '#64748b',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px'
              }}
            >
              {isPassed ? <CheckCircle2 size={12} color="#34d399" /> : null}
              <span>{st.label}</span>
            </div>
          );
        })}
      </div>

      {/* Description Banner */}
      <div style={{
        background: 'rgba(15, 23, 42, 0.9)',
        border: '1px solid rgba(56, 189, 248, 0.2)',
        borderRadius: '6px',
        padding: '8px 12px',
        fontSize: '0.78rem',
        color: '#cbd5e1',
        lineHeight: 1.4
      }}>
        {stepDescription}
      </div>

    </div>
  );
};
