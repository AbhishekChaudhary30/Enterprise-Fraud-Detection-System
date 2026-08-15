import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

interface Stats {
  total_predictions: number;
  fraud_detected: number;
  fraud_rate: number;
  risk_distribution: { low: number; medium: number; high: number };
  model_version: string;
  model_algorithm: string;
  avg_probability: number;
  investigation_counts: Record<string, number>;
  model_metrics: Record<string, number>;
}

interface RecentPrediction {
  prediction_id: string;
  prediction_timestamp: string;
  fraud_probability: number;
  risk_score: number;
  risk_level: string;
  decision: string;
  model_version: string;
}

const RISK_COLORS = { LOW: '#10b981', MEDIUM: '#f59e0b', HIGH: '#ef4444' };

function MetricCard({ label, value, sub, color }: { label: string; value: string | number; sub?: string; color?: string }) {
  return (
    <div style={{
      background: '#0f172a',
      border: '1px solid #1e293b',
      borderRadius: '12px',
      padding: '20px',
      minWidth: 0,
    }}>
      <p style={{ fontSize: '12px', color: '#64748b', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</p>
      <p style={{ fontSize: '28px', fontWeight: 700, color: color || '#f1f5f9', marginTop: '8px', letterSpacing: '-0.02em' }}>{value}</p>
      {sub && <p style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>{sub}</p>}
    </div>
  );
}

function RiskBadge({ level }: { level: string }) {
  const colors: Record<string, { bg: string; text: string }> = {
    LOW: { bg: 'rgba(16,185,129,0.15)', text: '#10b981' },
    MEDIUM: { bg: 'rgba(245,158,11,0.15)', text: '#f59e0b' },
    HIGH: { bg: 'rgba(239,68,68,0.15)', text: '#ef4444' },
  };
  const c = colors[level] || colors.LOW;
  return (
    <span style={{
      padding: '3px 10px',
      borderRadius: '12px',
      fontSize: '11px',
      fontWeight: 600,
      background: c.bg,
      color: c.text,
    }}>
      {level}
    </span>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [recent, setRecent] = useState<RecentPrediction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [s, r] = await Promise.all([
          api.getDashboardStats() as Promise<Stats>,
          api.getRecentPredictions() as Promise<{ predictions: RecentPrediction[] }>,
        ]);
        setStats(s);
        setRecent(r.predictions);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <div style={{ color: '#64748b', padding: '40px' }}>Loading dashboard...</div>;
  if (!stats) return <div style={{ color: '#ef4444', padding: '40px' }}>Failed to load dashboard data</div>;

  const riskData = [
    { name: 'Low Risk', value: stats.risk_distribution.low, color: RISK_COLORS.LOW },
    { name: 'Medium Risk', value: stats.risk_distribution.medium, color: RISK_COLORS.MEDIUM },
    { name: 'High Risk', value: stats.risk_distribution.high, color: RISK_COLORS.HIGH },
  ].filter(d => d.value > 0);

  const metrics = stats.model_metrics || {};

  const [isResetting, setIsResetting] = useState(false);

  const handleReset = async () => {
    if (!window.confirm("Are you sure you want to reset the dashboard? Current predictions will be archived to History and your dashboard will drop to zero.")) {
      return;
    }
    setIsResetting(true);
    try {
      await api.resetDashboard();
      // Reload stats
      const [s, r] = await Promise.all([
        api.getDashboardStats() as Promise<Stats>,
        api.getRecentPredictions() as Promise<{ predictions: RecentPrediction[] }>,
      ]);
      setStats(s);
      setRecent(r.predictions);
    } catch (err) {
      console.error('Failed to reset dashboard:', err);
      alert('Failed to reset dashboard');
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '32px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#f1f5f9' }}>Dashboard</h1>
          <p style={{ fontSize: '14px', color: '#64748b', marginTop: '4px' }}>Real-time fraud intelligence overview</p>
        </div>
        <button
          onClick={handleReset}
          disabled={isResetting}
          style={{
            background: 'transparent',
            border: '1px solid #ef4444',
            color: '#ef4444',
            padding: '8px 16px',
            borderRadius: '8px',
            cursor: isResetting ? 'not-allowed' : 'pointer',
            fontSize: '13px',
            fontWeight: 600,
            opacity: isResetting ? 0.5 : 1,
            transition: 'all 0.2s',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
          onMouseOver={(e) => {
            if (!isResetting) e.currentTarget.style.background = 'rgba(239,68,68,0.1)';
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.background = 'transparent';
          }}
        >
          {isResetting ? 'Resetting...' : '🔄 Reset Dashboard'}
        </button>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '32px' }}>
        <MetricCard label="Total Predictions" value={stats.total_predictions.toLocaleString()} />
        <MetricCard label="Fraud Detected" value={stats.fraud_detected.toLocaleString()} color="#ef4444" />
        <MetricCard label="Fraud Rate" value={`${(stats.fraud_rate * 100).toFixed(2)}%`} />
        <MetricCard label="High Risk" value={stats.risk_distribution.high} color="#ef4444" />
        <MetricCard label="Model" value={stats.model_version} sub={stats.model_algorithm} />
        <MetricCard label="PR-AUC" value={metrics.pr_auc ? metrics.pr_auc.toFixed(4) : 'N/A'} color="#6366f1" />
        <MetricCard label="Precision" value={metrics.precision ? metrics.precision.toFixed(4) : 'N/A'} />
        <MetricCard label="Recall" value={metrics.recall ? metrics.recall.toFixed(4) : 'N/A'} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px' }}>
        {/* Risk Distribution Chart */}
        <div style={{
          background: '#0f172a',
          border: '1px solid #1e293b',
          borderRadius: '12px',
          padding: '24px',
        }}>
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#f1f5f9', marginBottom: '16px' }}>Risk Distribution</h3>
          {riskData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={riskData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} strokeWidth={0}>
                  {riskData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Pie>
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p style={{ color: '#64748b', fontSize: '13px', textAlign: 'center', paddingTop: '60px' }}>No predictions yet</p>
          )}
          <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', marginTop: '12px' }}>
            {Object.entries(RISK_COLORS).map(([level, color]) => (
              <div key={level} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#94a3b8' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: color }} />
                {level}
              </div>
            ))}
          </div>
        </div>

        {/* Recent Predictions Table */}
        <div style={{
          background: '#0f172a',
          border: '1px solid #1e293b',
          borderRadius: '12px',
          padding: '24px',
          overflow: 'auto',
        }}>
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#f1f5f9', marginBottom: '16px' }}>Recent Predictions</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #1e293b' }}>
                {['Time', 'Probability', 'Risk', 'Score', 'Decision', 'Model'].map(h => (
                  <th key={h} style={{ padding: '8px 12px', textAlign: 'left', color: '#64748b', fontWeight: 500, fontSize: '11px', textTransform: 'uppercase' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {recent.length === 0 ? (
                <tr><td colSpan={6} style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>No predictions yet. Score a transaction to get started.</td></tr>
              ) : recent.map(p => (
                <tr key={p.prediction_id} style={{ borderBottom: '1px solid rgba(30,41,59,0.5)' }}>
                  <td style={{ padding: '10px 12px', color: '#94a3b8' }}>{new Date(p.prediction_timestamp).toLocaleTimeString()}</td>
                  <td style={{ padding: '10px 12px', color: '#f1f5f9', fontFamily: 'monospace' }}>{p.fraud_probability.toFixed(4)}</td>
                  <td style={{ padding: '10px 12px' }}><RiskBadge level={p.risk_level} /></td>
                  <td style={{ padding: '10px 12px', color: '#f1f5f9' }}>{p.risk_score}</td>
                  <td style={{ padding: '10px 12px', color: '#94a3b8' }}>{p.decision}</td>
                  <td style={{ padding: '10px 12px', color: '#64748b' }}>{p.model_version}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
