import { useState } from 'react';
import { api } from '../services/api';

export default function BatchPage() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<{ blob: Blob; summary: string } | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<string[][]>([]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) {
      setFile(f);
      setResult(null);
      setError('');
      // Preview first 5 rows
      const reader = new FileReader();
      reader.onload = () => {
        const text = reader.result as string;
        const rows = text.split('\n').slice(0, 6).map(r => r.split(','));
        setPreview(rows);
      };
      reader.readAsText(f);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setError('');
    setLoading(true);
    try {
      const blob = await api.uploadCsv(file);
      const text = await blob.text();
      const lines = text.split('\n').filter(l => l.trim());
      const header = lines[0]?.split(',') || [];
      const riskIdx = header.indexOf('risk_level');
      const highCount = lines.slice(1).filter(l => l.split(',')[riskIdx] === 'HIGH').length;
      const medCount = lines.slice(1).filter(l => l.split(',')[riskIdx] === 'MEDIUM').length;
      const lowCount = lines.slice(1).filter(l => l.split(',')[riskIdx] === 'LOW').length;
      setResult({
        blob: new Blob([text], { type: 'text/csv' }),
        summary: `${lines.length - 1} transactions scored | ${highCount} HIGH | ${medCount} MEDIUM | ${lowCount} LOW`,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!result) return;
    const url = URL.createObjectURL(result.blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `predictions_${file?.name || 'results.csv'}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#f1f5f9' }}>Batch Prediction</h1>
        <p style={{ fontSize: '14px', color: '#64748b', marginTop: '4px' }}>Upload a CSV file to score multiple transactions at once</p>
      </div>

      <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '32px' }}>
        {/* Upload area */}
        <div style={{
          border: '2px dashed #334155', borderRadius: '12px', padding: '40px', textAlign: 'center',
          background: file ? 'rgba(99,102,241,0.05)' : 'transparent',
        }}>
          <input type="file" accept=".csv" onChange={handleFileSelect}
            style={{ display: 'none' }} id="csv-upload" />
          <label htmlFor="csv-upload" style={{ cursor: 'pointer' }}>
            <span style={{ fontSize: '40px', display: 'block', marginBottom: '12px' }}>📁</span>
            <p style={{ fontSize: '14px', color: '#94a3b8' }}>
              {file ? file.name : 'Click to select a CSV file'}
            </p>
            {file && <p style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>{(file.size / 1024).toFixed(1)} KB</p>}
          </label>
        </div>

        {/* Preview */}
        {preview.length > 0 && (
          <div style={{ marginTop: '24px', overflow: 'auto' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 600, color: '#f1f5f9', marginBottom: '12px' }}>Preview (first 5 rows)</h4>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr>
                  {preview[0]?.map((h, i) => (
                    <th key={i} style={{ padding: '6px 10px', textAlign: 'left', color: '#64748b', borderBottom: '1px solid #1e293b', fontWeight: 500, whiteSpace: 'nowrap' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.slice(1).map((row, i) => (
                  <tr key={i}>
                    {row.map((cell, j) => (
                      <td key={j} style={{ padding: '6px 10px', color: '#94a3b8', borderBottom: '1px solid rgba(30,41,59,0.5)', whiteSpace: 'nowrap' }}>
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {error && (
          <div style={{ marginTop: '16px', padding: '10px 14px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '8px', color: '#fca5a5', fontSize: '13px' }}>
            {error}
          </div>
        )}

        {/* Actions */}
        <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
          <button onClick={handleUpload} disabled={!file || loading} style={{
            padding: '12px 24px',
            background: !file || loading ? '#334155' : 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
            color: '#fff', border: 'none', borderRadius: '8px', fontSize: '14px', fontWeight: 600,
            cursor: !file || loading ? 'not-allowed' : 'pointer',
          }}>
            {loading ? 'Processing...' : '🚀 Score Transactions'}
          </button>

          {result && (
            <button onClick={handleDownload} style={{
              padding: '12px 24px', background: '#10b981', color: '#fff',
              border: 'none', borderRadius: '8px', fontSize: '14px', fontWeight: 600, cursor: 'pointer',
            }}>
              📥 Download Results
            </button>
          )}
        </div>

        {/* Results summary */}
        {result && (
          <div style={{
            marginTop: '24px', padding: '16px', background: 'rgba(16,185,129,0.1)',
            border: '1px solid rgba(16,185,129,0.3)', borderRadius: '8px',
          }}>
            <p style={{ fontSize: '14px', fontWeight: 600, color: '#10b981' }}>✅ Batch Scoring Complete</p>
            <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>{result.summary}</p>
          </div>
        )}
      </div>
    </div>
  );
}
