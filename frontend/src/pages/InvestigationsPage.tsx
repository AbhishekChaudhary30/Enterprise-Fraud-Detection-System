import { useEffect, useState } from 'react';
import { api } from '../services/api';

interface Investigation {
  id: number;
  prediction_id: string;
  status: string;
  priority: string;
  assigned_to: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  NEW: { bg: 'rgba(59,130,246,0.15)', text: '#3b82f6' },
  UNDER_REVIEW: { bg: 'rgba(245,158,11,0.15)', text: '#f59e0b' },
  CONFIRMED_FRAUD: { bg: 'rgba(239,68,68,0.15)', text: '#ef4444' },
  FALSE_POSITIVE: { bg: 'rgba(16,185,129,0.15)', text: '#10b981' },
  RESOLVED: { bg: 'rgba(148,163,184,0.15)', text: '#94a3b8' },
};

const STATUSES = ['NEW', 'UNDER_REVIEW', 'CONFIRMED_FRAUD', 'FALSE_POSITIVE', 'RESOLVED'];

export default function InvestigationsPage() {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [filter, setFilter] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<number | null>(null);

  const load = async () => {
    try {
      const res = await api.getInvestigations(filter || undefined) as {
        investigations: Investigation[];
        status_counts: Record<string, number>;
      };
      setInvestigations(res.investigations);
      setCounts(res.status_counts);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [filter]);

  const handleStatusUpdate = async (id: number, newStatus: string) => {
    setUpdating(id);
    try {
      await api.updateInvestigation(id, newStatus);
      await load();
    } catch (err) {
      console.error(err);
    } finally {
      setUpdating(null);
    }
  };

  const total = Object.values(counts).reduce((a, b) => a + b, 0);

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#f1f5f9' }}>Investigations</h1>
        <p style={{ fontSize: '14px', color: '#64748b', marginTop: '4px' }}>Manage fraud investigation workflows</p>
      </div>

      {/* Status counts */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', flexWrap: 'wrap' }}>
        <button onClick={() => setFilter(null)} style={{
          padding: '8px 16px', borderRadius: '8px', fontSize: '13px', fontWeight: 500,
          background: !filter ? '#6366f1' : '#1e293b', color: !filter ? '#fff' : '#94a3b8',
          border: !filter ? 'none' : '1px solid #334155', cursor: 'pointer',
        }}>
          All ({total})
        </button>
        {STATUSES.map(s => {
          const c = STATUS_COLORS[s];
          return (
            <button key={s} onClick={() => setFilter(s)} style={{
              padding: '8px 16px', borderRadius: '8px', fontSize: '13px', fontWeight: 500,
              background: filter === s ? c.text : '#1e293b', color: filter === s ? '#fff' : c.text,
              border: `1px solid ${filter === s ? c.text : '#334155'}`, cursor: 'pointer',
            }}>
              {s.replace(/_/g, ' ')} ({counts[s] || 0})
            </button>
          );
        })}
      </div>

      {/* Table */}
      <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', overflow: 'auto' }}>
        {loading ? (
          <p style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>Loading...</p>
        ) : investigations.length === 0 ? (
          <p style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
            No investigations found. High-risk predictions automatically create investigations.
          </p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #1e293b' }}>
                {['ID', 'Prediction', 'Status', 'Priority', 'Assigned To', 'Created', 'Actions'].map(h => (
                  <th key={h} style={{ padding: '12px 16px', textAlign: 'left', color: '#64748b', fontWeight: 500, fontSize: '11px', textTransform: 'uppercase' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {investigations.map(inv => {
                const sc = STATUS_COLORS[inv.status] || STATUS_COLORS.NEW;
                return (
                  <tr key={inv.id} style={{ borderBottom: '1px solid rgba(30,41,59,0.5)' }}>
                    <td style={{ padding: '12px 16px', color: '#f1f5f9', fontWeight: 500 }}>#{inv.id}</td>
                    <td style={{ padding: '12px 16px', color: '#94a3b8', fontFamily: 'monospace', fontSize: '11px' }}>
                      {inv.prediction_id.slice(0, 8)}...
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{ padding: '3px 10px', borderRadius: '12px', fontSize: '11px', fontWeight: 600, background: sc.bg, color: sc.text }}>
                        {inv.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px', color: '#94a3b8' }}>{inv.priority}</td>
                    <td style={{ padding: '12px 16px', color: '#94a3b8' }}>{inv.assigned_to || '—'}</td>
                    <td style={{ padding: '12px 16px', color: '#64748b' }}>
                      {new Date(inv.created_at).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <select
                        disabled={updating === inv.id}
                        value={inv.status}
                        onChange={e => handleStatusUpdate(inv.id, e.target.value)}
                        style={{
                          padding: '4px 8px', background: '#1e293b', border: '1px solid #334155',
                          borderRadius: '6px', color: '#f1f5f9', fontSize: '12px', cursor: 'pointer',
                        }}
                      >
                        {STATUSES.map(s => (
                          <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
                        ))}
                      </select>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
