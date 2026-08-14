import { useEffect, useState } from 'react';
import { api } from '../services/api';

interface MonitoringData {
  prediction_volume: number;
  fraud_prediction_rate: number;
  risk_distribution: { low: number; medium: number; high: number };
  model_version: string;
  model_loaded: boolean;
  avg_latency_ms: number;
  error_count: number;
  request_count: number;
  uptime_seconds: number;
}

interface DriftReport {
  drift_reports: Record<string, {
    generated_at: string;
    drift_detected: boolean;
    findings: { name: string; statistic: number; p_value: number; drifted: boolean }[];
  }>;
  reports_available: number;
}

function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span style={{
      display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%',
      background: ok ? '#10b981' : '#ef4444', marginRight: '6px',
      boxShadow: ok ? '0 0 8px rgba(16,185,129,0.5)' : '0 0 8px rgba(239,68,68,0.5)',
    }} />
  );
}

function formatUptime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

export default function MonitoringPage() {
  const [overview, setOverview] = useState<MonitoringData | null>(null);
  const [drift, setDrift] = useState<DriftReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [o, d] = await Promise.all([
          api.getMonitoringOverview() as Promise<MonitoringData>,
          api.getDriftReport() as Promise<DriftReport>,
        ]);
        setOverview(o);
        setDrift(d);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <div style={{ color: '#64748b', padding: '40px' }}>Loading monitoring data...</div>;
  if (!overview) return <div style={{ color: '#ef4444', padding: '40px' }}>Failed to load monitoring data</div>;

  const healthChecks = [
    { name: 'ML Model', ok: overview.model_loaded, detail: overview.model_version },
    { name: 'API Server', ok: true, detail: `${overview.request_count} requests` },
    { name: 'Error Rate', ok: overview.error_count === 0, detail: `${overview.error_count} errors` },
    { name: 'Latency', ok: overview.avg_latency_ms < 1000, detail: `${overview.avg_latency_ms.toFixed(1)}ms avg` },
  ];

  const driftReports = drift?.drift_reports || {};

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#f1f5f9' }}>System Monitoring</h1>
        <p style={{ fontSize: '14px', color: '#64748b', marginTop: '4px' }}>Real-time system health, performance, and drift detection</p>
      </div>

      {/* Health checks */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px', marginBottom: '24px',
      }}>
        {healthChecks.map(check => (
          <div key={check.name} style={{
            background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '16px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '13px', color: '#f1f5f9', fontWeight: 500 }}>
                <StatusDot ok={check.ok} />{check.name}
              </span>
              <span style={{
                padding: '2px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: 600,
                background: check.ok ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
                color: check.ok ? '#10b981' : '#ef4444',
              }}>
                {check.ok ? 'HEALTHY' : 'WARNING'}
              </span>
            </div>
            <p style={{ fontSize: '12px', color: '#64748b', marginTop: '6px' }}>{check.detail}</p>
          </div>
        ))}
      </div>

      {/* Operational metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
        <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '24px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#f1f5f9', marginBottom: '16px' }}>Operational Metrics</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
            {[
              { label: 'Prediction Volume', value: overview.prediction_volume.toLocaleString() },
              { label: 'Fraud Rate', value: `${(overview.fraud_prediction_rate * 100).toFixed(2)}%` },
              { label: 'Avg Latency', value: `${overview.avg_latency_ms.toFixed(1)}ms` },
              { label: 'Uptime', value: formatUptime(overview.uptime_seconds) },
              { label: 'Total Requests', value: overview.request_count.toLocaleString() },
              { label: 'Errors', value: overview.error_count.toString() },
            ].map(m => (
              <div key={m.label} style={{ padding: '12px', background: '#1e293b', borderRadius: '8px' }}>
                <p style={{ fontSize: '11px', color: '#64748b' }}>{m.label}</p>
                <p style={{ fontSize: '18px', fontWeight: 600, color: '#f1f5f9', marginTop: '2px' }}>{m.value}</p>
              </div>
            ))}
          </div>
        </div>

        <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '24px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#f1f5f9', marginBottom: '16px' }}>Risk Distribution</h3>
          <div style={{ display: 'flex', gap: '16px', marginTop: '12px' }}>
            {[
              { label: 'Low Risk', value: overview.risk_distribution.low, color: '#10b981' },
              { label: 'Medium Risk', value: overview.risk_distribution.medium, color: '#f59e0b' },
              { label: 'High Risk', value: overview.risk_distribution.high, color: '#ef4444' },
            ].map(r => (
              <div key={r.label} style={{ flex: 1, textAlign: 'center', padding: '16px', background: '#1e293b', borderRadius: '8px' }}>
                <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: r.color, margin: '0 auto 8px' }} />
                <p style={{ fontSize: '24px', fontWeight: 700, color: r.color }}>{r.value}</p>
                <p style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>{r.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Drift detection */}
      <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '24px' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#f1f5f9', marginBottom: '16px' }}>Drift Detection</h3>
        {Object.keys(driftReports).length === 0 ? (
          <p style={{ color: '#64748b', fontSize: '13px' }}>No drift reports available. Run <code style={{ background: '#1e293b', padding: '2px 6px', borderRadius: '4px' }}>python scripts/run_drift.py</code> to generate drift analysis.</p>
        ) : (
          <div style={{ display: 'grid', gap: '16px' }}>
            {Object.entries(driftReports).map(([name, report]) => (
              <div key={name} style={{ padding: '16px', background: '#1e293b', borderRadius: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <h4 style={{ fontSize: '13px', fontWeight: 600, color: '#f1f5f9' }}>{name.replace(/_/g, ' ').toUpperCase()}</h4>
                  <span style={{
                    padding: '3px 10px', borderRadius: '12px', fontSize: '11px', fontWeight: 600,
                    background: report.drift_detected ? 'rgba(239,68,68,0.15)' : 'rgba(16,185,129,0.15)',
                    color: report.drift_detected ? '#ef4444' : '#10b981',
                  }}>
                    {report.drift_detected ? 'DRIFT DETECTED' : 'NO DRIFT'}
                  </span>
                </div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>
                  {report.findings?.length || 0} features analyzed | Generated: {new Date(report.generated_at).toLocaleString()}
                </div>
                {report.findings?.filter(f => f.drifted).length > 0 && (
                  <div style={{ marginTop: '8px', fontSize: '12px', color: '#f59e0b' }}>
                    ⚠ Drifted features: {report.findings.filter(f => f.drifted).map(f => f.name).join(', ')}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
