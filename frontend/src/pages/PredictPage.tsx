import { useState } from 'react';
import { api } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface PredictionResult {
  prediction_id: string;
  fraud_probability: number;
  risk_score: number;
  risk_level: string;
  decision: string;
  model_version: string;
  threshold: number;
  execution_time_ms: number;
  explanation: { feature: string; shap_value: number; direction: string }[];
}

// Default features for the creditcard dataset
const DEFAULT_FEATURES: Record<string, number> = {
  Time: 0, V1: -1.36, V2: -0.07, V3: 2.54, V4: 1.38, V5: -0.34,
  V6: 0.46, V7: 0.24, V8: 0.10, V9: 0.36, V10: 0.09,
  V11: -0.55, V12: -0.62, V13: -0.99, V14: -0.31, V15: 1.47,
  V16: -0.47, V17: 0.21, V18: 0.03, V19: 0.40, V20: 0.25,
  V21: -0.02, V22: 0.28, V23: -0.11, V24: -0.34, V25: -0.72,
  V26: -0.05, V27: -0.03, V28: -0.01, Amount: 149.62,
};

function RiskGauge({ probability, riskLevel }: { probability: number; riskLevel: string }) {
  const pct = probability * 100;
  const color = riskLevel === 'HIGH' ? '#ef4444' : riskLevel === 'MEDIUM' ? '#f59e0b' : '#10b981';
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{
        width: '160px', height: '160px', borderRadius: '50%', margin: '0 auto',
        background: `conic-gradient(${color} ${pct * 3.6}deg, #1e293b ${pct * 3.6}deg)`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <div style={{
          width: '120px', height: '120px', borderRadius: '50%', background: '#0f172a',
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{ fontSize: '28px', fontWeight: 700, color }}>{pct.toFixed(1)}%</span>
          <span style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>Fraud Probability</span>
        </div>
      </div>
      <div style={{
        marginTop: '12px', display: 'inline-block', padding: '4px 16px', borderRadius: '12px', fontSize: '13px', fontWeight: 600,
        background: `${color}20`, color,
      }}>
        {riskLevel} RISK — {(probability < 0.15 ? 'APPROVE' : probability < 0.5 ? 'REVIEW' : 'REJECT')}
      </div>
    </div>
  );
}

export default function PredictPage() {
  const [features, setFeatures] = useState<Record<string, number>>({ ...DEFAULT_FEATURES });
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<'form' | 'json'>('form');
  const [jsonInput, setJsonInput] = useState(JSON.stringify(DEFAULT_FEATURES, null, 2));

  const handlePredict = async () => {
    setError('');
    setLoading(true);
    try {
      const input = mode === 'json' ? JSON.parse(jsonInput) : features;
      const res = await api.predict(input) as PredictionResult;
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Prediction failed');
    } finally {
      setLoading(false);
    }
  };

  const shapData = result?.explanation?.slice(0, 10).map(e => ({
    feature: e.feature.length > 15 ? e.feature.slice(0, 15) + '…' : e.feature,
    value: e.shap_value,
    direction: e.direction,
  })) || [];

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#f1f5f9' }}>Transaction Scoring</h1>
        <p style={{ fontSize: '14px', color: '#64748b', marginTop: '4px' }}>Score a transaction for fraud risk with real-time ML prediction and SHAP explanation</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* Input */}
        <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '24px' }}>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
            {(['form', 'json'] as const).map(m => (
              <button key={m} onClick={() => setMode(m)} style={{
                padding: '6px 16px', borderRadius: '6px', fontSize: '13px', fontWeight: 500,
                background: mode === m ? '#6366f1' : 'transparent', color: mode === m ? '#fff' : '#94a3b8',
                border: mode === m ? 'none' : '1px solid #334155', cursor: 'pointer',
              }}>
                {m === 'form' ? 'Form' : 'JSON'}
              </button>
            ))}
          </div>

          {mode === 'form' ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', maxHeight: '400px', overflowY: 'auto' }}>
              {Object.entries(features).map(([key, val]) => (
                <div key={key}>
                  <label style={{ fontSize: '11px', color: '#64748b', display: 'block', marginBottom: '2px' }}>{key}</label>
                  <input type="number" step="any" value={val}
                    onChange={e => setFeatures({ ...features, [key]: parseFloat(e.target.value) || 0 })}
                    style={{
                      width: '100%', padding: '6px 8px', background: '#1e293b', border: '1px solid #334155',
                      borderRadius: '6px', color: '#f1f5f9', fontSize: '12px', outline: 'none',
                    }}
                  />
                </div>
              ))}
            </div>
          ) : (
            <textarea value={jsonInput} onChange={e => setJsonInput(e.target.value)}
              style={{
                width: '100%', height: '400px', padding: '12px', background: '#1e293b', border: '1px solid #334155',
                borderRadius: '8px', color: '#f1f5f9', fontSize: '13px', fontFamily: 'monospace', outline: 'none', resize: 'none',
              }}
            />
          )}

          {error && <div style={{ marginTop: '12px', padding: '8px 12px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '8px', color: '#fca5a5', fontSize: '13px' }}>{error}</div>}

          <button onClick={handlePredict} disabled={loading} style={{
            width: '100%', marginTop: '16px', padding: '12px',
            background: loading ? '#4338ca' : 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
            color: '#fff', border: 'none', borderRadius: '8px', fontSize: '14px', fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
          }}>
            {loading ? 'Scoring...' : '🎯 Score Transaction'}
          </button>
        </div>

        {/* Result */}
        <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '24px' }}>
          {!result ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#475569', fontSize: '14px' }}>
              Submit a transaction to see results
            </div>
          ) : (
            <div>
              <RiskGauge probability={result.fraud_probability} riskLevel={result.risk_level} />

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px', marginTop: '24px' }}>
                {[
                  { label: 'Risk Score', value: result.risk_score },
                  { label: 'Threshold', value: result.threshold.toFixed(4) },
                  { label: 'Model', value: result.model_version },
                  { label: 'Latency', value: `${result.execution_time_ms.toFixed(1)}ms` },
                ].map(m => (
                  <div key={m.label} style={{ padding: '10px', background: '#1e293b', borderRadius: '8px' }}>
                    <p style={{ fontSize: '11px', color: '#64748b' }}>{m.label}</p>
                    <p style={{ fontSize: '16px', fontWeight: 600, color: '#f1f5f9', marginTop: '2px' }}>{m.value}</p>
                  </div>
                ))}
              </div>

              {/* SHAP Explanation */}
              {shapData.length > 0 && (
                <div style={{ marginTop: '24px' }}>
                  <h4 style={{ fontSize: '13px', fontWeight: 600, color: '#f1f5f9', marginBottom: '12px' }}>Feature Contributions (SHAP)</h4>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={shapData} layout="vertical" margin={{ left: 60 }}>
                      <XAxis type="number" tick={{ fontSize: 11, fill: '#64748b' }} />
                      <YAxis type="category" dataKey="feature" tick={{ fontSize: 11, fill: '#94a3b8' }} width={60} />
                      <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9', fontSize: '12px' }} />
                      <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                        {shapData.map((e, i) => (
                          <Cell key={i} fill={e.direction === 'increases_risk' ? '#ef4444' : '#10b981'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              <p style={{ fontSize: '11px', color: '#475569', marginTop: '16px', textAlign: 'center' }}>
                ID: {result.prediction_id}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
