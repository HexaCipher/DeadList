import { useLocation } from 'react-router-dom';
import { Shield, Download, Wifi, WifiOff } from 'lucide-react';
import useAnalysisStore from '../../store/analysisStore';
import { downloadReport } from '../../utils/api';
import { getRiskLevelColor } from '../../utils/scoring';

export default function Header() {
  const location = useLocation();
  const currentAnalysis = useAnalysisStore((s) => s.currentAnalysis);
  const analysisStatus = useAnalysisStore((s) => s.analysisStatus);

  const getPageTitle = () => {
    if (location.pathname === '/') return 'Upload Memory Dump';
    if (location.pathname.startsWith('/analysis')) return 'Live Analysis';
    if (location.pathname.startsWith('/dashboard')) return 'Analysis Dashboard';
    if (location.pathname === '/history') return 'Analysis History';
    return 'DeadList';
  };

  const handleExportPDF = async () => {
    if (!currentAnalysis?.id) return;
    try {
      const response = await downloadReport(currentAnalysis.id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `DeadList_Report_${currentAnalysis.filename || 'analysis'}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('PDF export failed:', err);
    }
  };

  return (
    <header className="h-14 bg-bg-surface border-b border-border-subtle flex items-center justify-between px-6 shrink-0">
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-semibold text-text-primary">{getPageTitle()}</h2>
        {currentAnalysis && (
          <div className="flex items-center gap-2 text-sm text-text-secondary">
            <span className="text-text-disabled">|</span>
            <span className="font-mono text-xs">{currentAnalysis.filename}</span>
            {currentAnalysis.risk_level && (
              <span
                className="badge text-[10px]"
                style={{
                  color: getRiskLevelColor(currentAnalysis.risk_level),
                  backgroundColor: `${getRiskLevelColor(currentAnalysis.risk_level)}15`,
                }}
              >
                {currentAnalysis.risk_level?.toUpperCase()}
              </span>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        {/* Export PDF button — only show on dashboard with complete analysis */}
        {location.pathname.startsWith('/dashboard') && currentAnalysis?.status === 'complete' && (
          <button
            onClick={handleExportPDF}
            className="flex items-center gap-2 px-3 py-1.5 bg-brand text-white text-sm
              font-medium rounded-btn hover:bg-brand/90 transition-colors glow-brand"
            id="export-pdf-btn"
          >
            <Download size={14} />
            Export PDF
          </button>
        )}

        {/* Connection status */}
        <div className="flex items-center gap-1.5 text-xs text-text-secondary">
          {analysisStatus === 'analyzing' ? (
            <>
              <Wifi size={14} className="text-accent-green" />
              <span className="text-accent-green">Live</span>
            </>
          ) : (
            <>
              <Shield size={14} className="text-text-disabled" />
              <span>v1.0</span>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
