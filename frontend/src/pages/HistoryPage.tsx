import { useEffect, useState } from 'react';
import { api } from '../services/api';

interface Prediction {
  prediction_id: string;
  prediction_timestamp: string;
  fraud_probability: number;
  risk_score: number;
  risk_level: string;
  decision: string;
  model_version: string;
}

export default function HistoryPage() {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const loadHistory = async () => {
    try {
      const data = await api.getHistory(500);
      setPredictions(data.history || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to permanently delete this prediction? This action cannot be undone and will delete any associated investigations.")) {
      return;
    }
    
    setDeletingId(id);
    try {
      await api.deletePrediction(id);
      await loadHistory();
    } catch (err) {
      console.error('Failed to delete prediction:', err);
      alert('Failed to delete prediction. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) return <div style={{ color: '#64748b', padding: '40px' }}>Loading history...</div>;

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#f1f5f9' }}>Prediction History</h1>
        <p style={{ fontSize: '14px', color: '#64748b', marginTop: '4px' }}>View and manage past predictions</p>
      </div>

      <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #1e293b', background: '#1e293b' }}>
                <th style={{ padding: '16px', fontSize: '12px', fontWeight: 600, color: '#94a3b8' }}>TIME</th>
                <th style={{ padding: '16px', fontSize: '12px', fontWeight: 600, color: '#94a3b8' }}>PREDICTION ID</th>
                <th style={{ padding: '16px', fontSize: '12px', fontWeight: 600, color: '#94a3b8' }}>PROBABILITY</th>
                <th style={{ padding: '16px', fontSize: '12px', fontWeight: 600, color: '#94a3b8' }}>RISK</th>
                <th style={{ padding: '16px', fontSize: '12px', fontWeight: 600, color: '#94a3b8' }}>SCORE</th>
                <th style={{ padding: '16px', fontSize: '12px', fontWeight: 600, color: '#94a3b8' }}>DECISION</th>
                <th style={{ padding: '16px', fontSize: '12px', fontWeight: 600, color: '#94a3b8' }}>MODEL</th>
                <th style={{ padding: '16px', fontSize: '12px', fontWeight: 600, color: '#94a3b8', textAlign: 'right' }}>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {predictions.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ padding: '32px', textAlign: 'center', color: '#64748b', fontSize: '13px' }}>
                    No prediction history found.
                  </td>
                </tr>
              ) : (
                predictions.map(p => (
                  <tr key={p.prediction_id} style={{ borderBottom: '1px solid #1e293b' }}>
                    <td style={{ padding: '16px', fontSize: '13px', color: '#94a3b8' }}>{new Date(p.prediction_timestamp).toLocaleString()}</td>
                    <td style={{ padding: '16px', fontSize: '13px', color: '#94a3b8', fontFamily: 'monospace' }}>{p.prediction_id.split('-')[0]}...</td>
                    <td style={{ padding: '16px', fontSize: '13px', color: '#f1f5f9', fontWeight: 500 }}>{p.fraud_probability.toFixed(4)}</td>
                    <td style={{ padding: '16px' }}>
                      <span style={{
                        padding: '4px 10px', borderRadius: '12px', fontSize: '11px', fontWeight: 600,
                        background: p.risk_level === 'HIGH' ? 'rgba(239,68,68,0.15)' : p.risk_level === 'MEDIUM' ? 'rgba(245,158,11,0.15)' : 'rgba(16,185,129,0.15)',
                        color: p.risk_level === 'HIGH' ? '#ef4444' : p.risk_level === 'MEDIUM' ? '#f59e0b' : '#10b981',
                      }}>
                        {p.risk_level}
                      </span>
                    </td>
                    <td style={{ padding: '16px', fontSize: '13px', color: '#94a3b8' }}>{p.risk_score}</td>
                    <td style={{ padding: '16px', fontSize: '13px', color: '#94a3b8' }}>{p.decision}</td>
                    <td style={{ padding: '16px', fontSize: '13px', color: '#94a3b8' }}>{p.model_version}</td>
                    <td style={{ padding: '16px', textAlign: 'right' }}>
                      <button 
                        onClick={() => handleDelete(p.prediction_id)}
                        disabled={deletingId === p.prediction_id}
                        style={{
                          background: 'transparent',
                          border: '1px solid #ef4444',
                          color: '#ef4444',
                          padding: '6px 12px',
                          borderRadius: '6px',
                          cursor: deletingId === p.prediction_id ? 'not-allowed' : 'pointer',
                          fontSize: '12px',
                          fontWeight: 500,
                          opacity: deletingId === p.prediction_id ? 0.5 : 1,
                          transition: 'all 0.2s',
                        }}
                        onMouseOver={(e) => {
                          if (deletingId !== p.prediction_id) {
                            e.currentTarget.style.background = 'rgba(239,68,68,0.1)';
                          }
                        }}
                        onMouseOut={(e) => {
                          e.currentTarget.style.background = 'transparent';
                        }}
                      >
                        {deletingId === p.prediction_id ? 'Deleting...' : 'Delete'}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
