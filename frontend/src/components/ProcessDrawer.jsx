import { useEffect, useState } from 'react';
import { X, Terminal, Network, AlertTriangle, FileCode2, BarChart3 } from 'lucide-react';
import useAnalysisStore from '../store/analysisStore';
import { getProcessDetail } from '../utils/api';
import { getScoreColor, getStatusBadgeClass, getScoreLabel } from '../utils/scoring';

export default function ProcessDrawer() {
  const selectedProcess = useAnalysisStore((s) => s.selectedProcess);
  const drawerOpen = useAnalysisStore((s) => s.drawerOpen);
  const closeDrawer = useAnalysisStore((s) => s.closeDrawer);
  const currentAnalysis = useAnalysisStore((s) => s.currentAnalysis);

  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetch detailed process data
  useEffect(() => {
    if (!selectedProcess || !currentAnalysis?.id) return;

    const fetchDetail = async () => {
      setLoading(true);
      try {
        const analysisId = currentAnalysis.id || currentAnalysis.analysis_id;
        const res = await getProcessDetail(analysisId, selectedProcess.pid);
        setDetail(res.data);
      } catch (err) {
        console.error('Failed to fetch process detail:', err);
        setDetail(null);
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [selectedProcess, currentAnalysis]);

  // Close on ESC
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') closeDrawer();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [closeDrawer]);

  if (!drawerOpen || !selectedProcess) return null;

  const proc = detail || selectedProcess;
  const connections = detail?.connections || [];
  const memRegions = detail?.memory_regions || [];
  const breakdown = detail?.score_breakdown || [];

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 drawer-overlay z-40"
        onClick={closeDrawer}
      />

      {/* Drawer */}
      <div className="fixed right-0 top-0 h-full w-[480px] bg-bg-surface border-l border-border-subtle
        z-50 overflow-y-auto animate-slide-in shadow-2xl">
        
        {/* Header */}
        <div className="sticky top-0 bg-bg-surface border-b border-border-subtle p-4 flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            <span className={getStatusBadgeClass(proc.status)}>{proc.status}</span>
            <h3 className="text-lg font-semibold text-text-primary">{proc.name}</h3>
          </div>
          <button
            onClick={closeDrawer}
            className="w-8 h-8 flex items-center justify-center rounded-md hover:bg-bg-elevated transition-colors text-text-secondary hover:text-text-primary"
            id="close-drawer-btn"
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-4 space-y-5">
          {/* Process Info */}
          <section>
            <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
              Process Information
            </h4>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'PID', value: proc.pid },
                { label: 'PPID', value: proc.ppid ?? 'N/A' },
                { label: 'In pslist', value: proc.in_pslist ? '✅ Yes' : '❌ No' },
                { label: 'In psscan', value: proc.in_psscan ? '✅ Yes' : '❌ No' },
                { label: 'Hidden (DKOM)', value: proc.is_hidden ? '🔴 YES' : '🟢 No' },
                { label: 'Injected Code', value: proc.has_injected_code ? '🔴 YES' : '🟢 No' },
              ].map(item => (
                <div key={item.label} className="bg-bg-elevated rounded-md p-2.5">
                  <p className="text-[10px] text-text-disabled uppercase">{item.label}</p>
                  <p className="text-sm font-mono text-text-primary mt-0.5">{item.value}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Suspicion Score */}
          <section>
            <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
              <BarChart3 size={14} />
              Suspicion Score
            </h4>
            <div className="bg-bg-elevated rounded-md p-4">
              <div className="flex items-center gap-3 mb-3">
                <span
                  className="text-3xl font-bold font-mono"
                  style={{ color: getScoreColor(proc.suspicion_score) }}
                >
                  {proc.suspicion_score}
                </span>
                <span className="text-sm text-text-secondary">/ 100</span>
                <span
                  className="badge ml-auto"
                  style={{
                    color: getScoreColor(proc.suspicion_score),
                    backgroundColor: `${getScoreColor(proc.suspicion_score)}15`,
                  }}
                >
                  {getScoreLabel(proc.suspicion_score)}
                </span>
              </div>
              <div className="w-full h-2 bg-bg-base rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${Math.min(proc.suspicion_score, 100)}%`,
                    backgroundColor: getScoreColor(proc.suspicion_score),
                  }}
                />
              </div>

              {/* Score Breakdown */}
              {breakdown.length > 0 && (
                <div className="mt-4 space-y-2">
                  {breakdown.map((item, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs">
                      <span className="shrink-0 font-mono font-bold" style={{ color: getScoreColor(item.points * 2) }}>
                        +{item.points}
                      </span>
                      <div>
                        <span className="text-text-primary font-medium">{item.criterion}</span>
                        <p className="text-text-disabled mt-0.5">{item.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>

          {/* Command Line */}
          <section>
            <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
              <Terminal size={14} />
              Command Line
            </h4>
            <div className="bg-bg-base border border-border-subtle rounded-md p-3">
              {proc.cmdline ? (
                <code className="font-mono text-xs text-text-primary break-all leading-relaxed">
                  {proc.cmdline}
                </code>
              ) : (
                <p className="text-accent-red text-xs font-mono italic">
                  Empty — No command line arguments (SUSPICIOUS)
                </p>
              )}
            </div>
          </section>

          {/* Network Connections */}
          {connections.length > 0 && (
            <section>
              <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
                <Network size={14} />
                Network Connections ({connections.length})
              </h4>
              <div className="space-y-2">
                {connections.map((conn, i) => (
                  <div key={i} className={`bg-bg-elevated rounded-md p-3 text-xs
                    ${conn.is_suspicious_port ? 'border border-accent-red/30' : ''}`}>
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-text-primary">
                        {conn.local_addr}:{conn.local_port}
                      </span>
                      <span className="text-text-disabled">→</span>
                      <span className={`font-mono ${conn.is_suspicious_port ? 'text-accent-red font-bold' : 'text-text-primary'}`}>
                        {conn.remote_addr}:{conn.remote_port}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-text-disabled">
                      <span>{conn.protocol}</span>
                      <span>•</span>
                      <span>{conn.state}</span>
                      {conn.country && (
                        <>
                          <span>•</span>
                          <span>{conn.city}, {conn.country}</span>
                        </>
                      )}
                      {conn.is_suspicious_port && (
                        <span className="text-accent-red font-bold ml-auto">⚠ SUSPICIOUS PORT</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Memory Regions (Malfind) */}
          {memRegions.length > 0 && (
            <section>
              <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
                <FileCode2 size={14} />
                <span className="text-accent-red">Suspicious Memory Regions ({memRegions.length})</span>
              </h4>
              <div className="space-y-3">
                {memRegions.map((region, i) => (
                  <div key={i} className="bg-bg-base border border-accent-red/20 rounded-md p-3">
                    <div className="flex items-center justify-between text-xs mb-2">
                      <span className="font-mono text-accent-red">{region.address}</span>
                      <span className="text-text-disabled">{region.protection}</span>
                    </div>
                    {region.tag && (
                      <p className="text-xs text-accent-amber font-medium mb-2">{region.tag}</p>
                    )}
                    {region.hex_dump && (
                      <pre className="font-mono text-[10px] text-text-secondary bg-bg-elevated
                        rounded p-2 overflow-x-auto whitespace-pre leading-relaxed">
                        {region.hex_dump}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      </div>
    </>
  );
}
