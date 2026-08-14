import { useEffect, useState } from 'react';
import { api } from '../services/api';

interface ModelData {
  versions: string[];
  latest: string;
}

interface ModelMetrics {
  metrics: Record<string, number>;
  model_version: string;
  model_algorithm: string;
  available: boolean;
}

interface ModelDetail {
  version: string;
  metadata: {
    selected_model: string;
    row_count: number;
    training_duration_seconds: number;
    comparisons: { model_name: string; validation_metrics: Record<string, number>; test_metrics: Record<string, number> }[];
  };
}

export default function ModelsPage() {
  const [models, setModels] = useState<ModelData | null>(null);
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [detail, setDetail] = useState<ModelDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [m, met, d] = await Promise.all([
          api.getModels() as Promise<ModelData>,
          api.getModelMetrics() as Promise<ModelMetrics>,
          api.getLatestModel() as Promise<ModelDetail>,
        ]);
        setModels(m);
        setMetrics(met);
        setDetail(d);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <div style={{ color: '#64748b', padding: '40px' }}>Loading models...</div>;

  const comparisons = detail?.metadata?.comparisons || [];
  const evalMetrics = metrics?.metrics || {};

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#f1f5f9' }}>Model Registry</h1>
        <p style={{ fontSize: '14px', color: '#64748b', marginTop: '4px' }}>Model versions, performance metrics, and comparison</p>
      </div>

      {/* Champion model card */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(139,92,246,0.1) 100%)',
        border: '1px solid rgba(99,102,241,0.3)',
        borderRadius: '12px', padding: '24px', marginBottom: '24px',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '20px' }}>👑</span>
              <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#f1f5f9' }}>Champion Model</h3>
            </div>
            <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>
              {models?.latest || 'N/A'} — {detail?.metadata?.selected_model || 'unknown'} — {detail?.metadata?.row_count?.toLocaleString()} training rows
            </p>
          </div>
          <div style={{ display: 'flex', gap: '16px' }}>
            {[
              { label: 'PR-AUC', value: evalMetrics.pr_auc },
              { label: 'ROC-AUC', value: evalMetrics.roc_auc },
              { label: 'F1', value: evalMetrics.f1 },
              { label: 'Precision', value: evalMetrics.precision },
              { label: 'Recall', value: evalMetrics.recall },
            ].map(m => (
              <div key={m.label} style={{ textAlign: 'center' }}>
                <p style={{ fontSize: '11px', color: '#64748b' }}>{m.label}</p>
                <p style={{ fontSize: '18px', fontWeight: 700, color: '#a5b4fc', marginTop: '2px' }}>
                  {m.value != null ? m.value.toFixed(4) : 'N/A'}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Model comparison table */}
      <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '24px', marginBottom: '24px' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#f1f5f9', marginBottom: '16px' }}>Training Comparison</h3>
        {comparisons.length === 0 ? (
          <p style={{ color: '#64748b', fontSize: '13px' }}>No model comparison data available</p>
        ) : (
          <div style={{ overflow: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #1e293b' }}>
                  {['Model', 'PR-AUC', 'ROC-AUC', 'F1', 'Precision', 'Recall', 'Status'].map(h => (
                    <th key={h} style={{ padding: '10px 16px', textAlign: 'left', color: '#64748b', fontWeight: 500, fontSize: '11px', textTransform: 'uppercase' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {comparisons.map(c => {
                  const isChampion = c.model_name === detail?.metadata?.selected_model;
                  const m = c.validation_metrics;
                  return (
                    <tr key={c.model_name} style={{
                      borderBottom: '1px solid rgba(30,41,59,0.5)',
                      background: isChampion ? 'rgba(99,102,241,0.05)' : 'transparent',
                    }}>
                      <td style={{ padding: '12px 16px', color: '#f1f5f9', fontWeight: isChampion ? 600 : 400 }}>
                        {c.model_name.replace(/_/g, ' ')}
                      </td>
                      <td style={{ padding: '12px 16px', color: '#f1f5f9', fontFamily: 'monospace' }}>{m.average_precision?.toFixed(4)}</td>
                      <td style={{ padding: '12px 16px', color: '#f1f5f9', fontFamily: 'monospace' }}>{m.roc_auc?.toFixed(4)}</td>
                      <td style={{ padding: '12px 16px', color: '#f1f5f9', fontFamily: 'monospace' }}>{m.f1?.toFixed(4)}</td>
                      <td style={{ padding: '12px 16px', color: '#f1f5f9', fontFamily: 'monospace' }}>{m.precision?.toFixed(4)}</td>
                      <td style={{ padding: '12px 16px', color: '#f1f5f9', fontFamily: 'monospace' }}>{m.recall?.toFixed(4)}</td>
                      <td style={{ padding: '12px 16px' }}>
                        {isChampion ? (
                          <span style={{ padding: '3px 10px', borderRadius: '12px', fontSize: '11px', fontWeight: 600, background: 'rgba(99,102,241,0.15)', color: '#a5b4fc' }}>
                            CHAMPION
                          </span>
                        ) : (
                          <span style={{ fontSize: '12px', color: '#64748b' }}>archived</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Available versions */}
      <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '24px' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#f1f5f9', marginBottom: '16px' }}>Registered Versions</h3>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {models?.versions?.map(v => (
            <div key={v} style={{
              padding: '8px 16px', borderRadius: '8px',
              background: v === models.latest ? 'rgba(99,102,241,0.15)' : '#1e293b',
              border: `1px solid ${v === models.latest ? 'rgba(99,102,241,0.3)' : '#334155'}`,
              color: v === models.latest ? '#a5b4fc' : '#94a3b8',
              fontSize: '13px', fontWeight: 500,
            }}>
              {v} {v === models.latest && '(latest)'}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
