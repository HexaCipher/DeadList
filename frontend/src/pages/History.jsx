import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Clock, FileText, Trash2, AlertTriangle, Shield, ChevronRight } from 'lucide-react';
import toast from 'react-hot-toast';
import { getHistory, deleteAnalysis } from '../utils/api';
import { formatBytes, formatTimestamp, getRiskLevelColor } from '../utils/scoring';

export default function HistoryPage() {
  const navigate = useNavigate();
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await getHistory();
      setAnalyses(res.data);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!confirm('Delete this analysis and its associated dump file?')) return;

    try {
      await deleteAnalysis(id);
      setAnalyses(analyses.filter(a => a.id !== id));
      toast.success('Analysis deleted');
    } catch (err) {
      toast.error('Failed to delete analysis');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-10 h-10 border-2 border-brand border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-text-primary">Analysis History</h2>
          <p className="text-sm text-text-secondary mt-1">
            {analyses.length} past analysis run{analyses.length !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      {analyses.length === 0 ? (
        <div className="card text-center py-16">
          <FileText size={40} className="mx-auto text-text-disabled mb-4" />
          <p className="text-text-secondary">No analysis runs yet.</p>
          <p className="text-text-disabled text-sm mt-1">
            Upload a memory dump to get started.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {analyses.map((analysis, i) => {
            const riskColor = getRiskLevelColor(analysis.risk_level);
            return (
              <div
                key={analysis.id}
                onClick={() => {
                  if (analysis.status === 'complete') {
                    navigate(`/dashboard/${analysis.id}`);
                  } else if (analysis.status === 'running') {
                    navigate(`/analysis/${analysis.id}`);
                  }
                }}
                className="card flex items-center gap-4 cursor-pointer hover:bg-bg-elevated/50
                  transition-colors animate-fade-in group"
                style={{ animationDelay: `${i * 50}ms` }}
              >
                {/* Risk indicator */}
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
                  style={{ backgroundColor: `${riskColor}15` }}
                >
                  {analysis.hidden_process_count > 0 ? (
                    <AlertTriangle size={18} style={{ color: riskColor }} />
                  ) : (
                    <Shield size={18} style={{ color: riskColor }} />
                  )}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-text-primary truncate">
                      {analysis.filename}
                    </p>
                    {analysis.risk_level && (
                      <span
                        className="badge text-[10px]"
                        style={{
                          color: riskColor,
                          backgroundColor: `${riskColor}15`,
                        }}
                      >
                        {analysis.risk_level.toUpperCase()}
                      </span>
                    )}
                    <span className={`badge text-[10px] ${
                      analysis.status === 'complete' ? 'badge-clean' :
                      analysis.status === 'running' ? 'badge-anomalous' :
                      analysis.status === 'failed' ? 'badge-critical' :
                      'badge-clean'
                    }`}>
                      {analysis.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-text-disabled">
                    <span className="flex items-center gap-1">
                      <Clock size={10} />
                      {formatTimestamp(analysis.created_at)}
                    </span>
                    <span>{formatBytes(analysis.file_size_bytes)}</span>
                    {analysis.hidden_process_count > 0 && (
                      <span className="text-accent-red font-semibold">
                        {analysis.hidden_process_count} hidden
                      </span>
                    )}
                    <span>{analysis.total_process_count || 0} processes</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={(e) => handleDelete(e, analysis.id)}
                    className="w-8 h-8 flex items-center justify-center rounded-md text-text-disabled
                      hover:text-accent-red hover:bg-accent-red/10 transition-colors opacity-0 group-hover:opacity-100"
                    title="Delete analysis"
                  >
                    <Trash2 size={14} />
                  </button>
                  <ChevronRight size={16} className="text-text-disabled group-hover:text-text-secondary transition-colors" />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
