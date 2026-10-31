import React, { useState, useRef } from 'react';
import { X, Upload, Image as ImageIcon, AlertTriangle, CheckCircle, Eye, Loader2 } from 'lucide-react';
import { uploadAgentVision } from '../../services/api';

interface VisionAnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirmFacts?: (facts: any) => void;
}

export const VisionAnalysisModal: React.FC<VisionAnalysisModalProps> = ({
  isOpen,
  onClose,
  onConfirmFacts
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [prompt, setPrompt] = useState<string>('Extract train IDs, delays, platforms, and operational status from this board.');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileChange = (selectedFile: File) => {
    if (!selectedFile.type.startsWith('image/')) {
      setError('Please select an image file (PNG, JPG, WebP).');
      return;
    }
    setError(null);
    setFile(selectedFile);
    setPreviewUrl(URL.createObjectURL(selectedFile));
    setResult(null);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const data = await uploadAgentVision(file, prompt);
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Vision analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleApply = () => {
    if (onConfirmFacts && result) {
      onConfirmFacts(result.extracted_facts || result);
    }
    onClose();
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(3, 7, 18, 0.85)',
        backdropFilter: 'blur(4px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px'
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '720px',
          maxHeight: '90vh',
          backgroundColor: '#09152b',
          borderRadius: '12px',
          border: '1px solid #1e3a6a',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid #14284b',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: '#0c1a35'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Eye size={20} color="#38bdf8" />
            <div>
              <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>
                Multimodal Visual Analyst
              </div>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                Gemma 4 (gemma-4-26b-a4b-it) Image Understanding for Station Displays & Signal Diagrams
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '4px'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Content Body */}
        <div style={{ padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Upload Area */}
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: '2px dashed #1e3a6a',
              borderRadius: '8px',
              padding: previewUrl ? '12px' : '32px',
              textAlign: 'center',
              backgroundColor: '#071224',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              style={{ display: 'none' }}
              onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
            />

            {previewUrl ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', width: '100%' }}>
                <img
                  src={previewUrl}
                  alt="Screenshot preview"
                  style={{
                    maxHeight: '220px',
                    maxWidth: '100%',
                    objectFit: 'contain',
                    borderRadius: '6px',
                    border: '1px solid #14284b'
                  }}
                />
                <span style={{ fontSize: '0.72rem', color: '#38bdf8' }}>Click or drop to replace image</span>
              </div>
            ) : (
              <>
                <Upload size={36} color="#0284c7" />
                <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#e2e8f0' }}>
                  Click to select screenshot or drag & drop here
                </div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                  Supports station display boards, signal interlocking diagrams, weather radar, timetable screenshots (PNG, JPG)
                </div>
              </>
            )}
          </div>

          {/* Prompt Field */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', marginBottom: '6px' }}>
              Vision Extraction Instruction:
            </label>
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. Extract train numbers, delays, and assigned platforms..."
              style={{
                width: '100%',
                backgroundColor: '#050b17',
                border: '1px solid #1e3a6a',
                borderRadius: '6px',
                padding: '8px 12px',
                color: '#f8fafc',
                fontSize: '0.8rem',
                outline: 'none',
                boxSizing: 'border-box'
              }}
            />
          </div>

          {/* Action Button */}
          <button
            onClick={handleAnalyze}
            disabled={!file || loading}
            style={{
              padding: '10px 16px',
              backgroundColor: !file || loading ? '#1e293b' : '#0284c7',
              color: !file || loading ? '#64748b' : '#ffffff',
              border: 'none',
              borderRadius: '6px',
              fontSize: '0.85rem',
              fontWeight: 700,
              cursor: !file || loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              transition: 'background-color 0.2s'
            }}
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Gemma 4 Multimodal Parsing...</span>
              </>
            ) : (
              <>
                <ImageIcon size={16} />
                <span>Analyze with Gemma 4 Vision</span>
              </>
            )}
          </button>

          {/* Error Notice */}
          {error && (
            <div
              style={{
                padding: '10px 14px',
                backgroundColor: '#450a0a',
                border: '1px solid #dc2626',
                borderRadius: '6px',
                color: '#fca5a5',
                fontSize: '0.78rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <AlertTriangle size={16} />
              <span>{error}</span>
            </div>
          )}

          {/* Extraction Results */}
          {result && (
            <div
              style={{
                backgroundColor: '#071224',
                borderRadius: '8px',
                border: '1px solid #14284b',
                padding: '14px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
              }}
            >
              {/* Mandatory Confirmation Notice */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  backgroundColor: '#451a03',
                  border: '1px solid #d97706',
                  borderRadius: '6px',
                  padding: '8px 12px',
                  color: '#fde68a',
                  fontSize: '0.75rem',
                  fontWeight: 600
                }}
              >
                <AlertTriangle size={16} color="#f59e0b" />
                <span>
                  CONTROLLER CONFIRMATION REQUIRED: Extracted facts are AI-interpreted. Verify against railway interlocking before confirming.
                </span>
              </div>

              {/* Parsed JSON facts */}
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', marginBottom: '6px' }}>
                  Structured Extracted Facts:
                </div>
                <pre
                  style={{
                    margin: 0,
                    padding: '10px',
                    backgroundColor: '#050b17',
                    borderRadius: '6px',
                    border: '1px solid #14284b',
                    color: '#e2e8f0',
                    fontSize: '0.75rem',
                    fontFamily: 'Consolas, Monaco, monospace',
                    maxHeight: '180px',
                    overflowY: 'auto',
                    whiteSpace: 'pre-wrap'
                  }}
                >
                  {JSON.stringify(result.extracted_facts || result, null, 2)}
                </pre>
              </div>

              {/* Confirm / Apply buttons */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button
                  onClick={onClose}
                  style={{
                    padding: '8px 14px',
                    backgroundColor: 'transparent',
                    border: '1px solid #334155',
                    borderRadius: '6px',
                    color: '#94a3b8',
                    fontSize: '0.8rem',
                    cursor: 'pointer'
                  }}
                >
                  Discard
                </button>
                <button
                  onClick={handleApply}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#10b981',
                    border: 'none',
                    borderRadius: '6px',
                    color: '#ffffff',
                    fontSize: '0.8rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <CheckCircle size={15} />
                  <span>Confirm & Import Facts</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
