import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Radar, ArrowRight, AlertTriangle, Shield } from 'lucide-react';
import useWebSocket from '../hooks/useWebSocket';
import useAnalysisStore from '../store/analysisStore';
import PluginStepper from '../components/PluginStepper';
import TerminalFeed from '../components/TerminalFeed';

export default function Analysis() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isConnected } = useWebSocket(id);
  const analysisStatus = useAnalysisStore((s) => s.analysisStatus);
  const overallProgress = useAnalysisStore((s) => s.overallProgress);
  const currentAnalysis = useAnalysisStore((s) => s.currentAnalysis);
  const wsMessages = useAnalysisStore((s) => s.wsMessages);

  const isComplete = analysisStatus === 'complete';
  const hasHidden = currentAnalysis?.hidden_process_count > 0;

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header with radar animation */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center
            ${isComplete
              ? hasHidden ? 'bg-accent-red/10 shadow-glow-red' : 'bg-accent-green/10 shadow-glow-green'
              : 'bg-accent-blue/10'
            }`}>
            {isComplete ? (
              hasHidden ? (
                <AlertTriangle size={24} className="text-accent-red" />
              ) : (
                <Shield size={24} className="text-accent-green" />
              )
            ) : (
              <Radar size={24} className="text-accent-blue animate-radar" />
            )}
          </div>
          <div>
            <h2 className="text-xl font-bold text-text-primary">
              {isComplete
                ? hasHidden ? '🚨 Threats Detected' : '✅ Analysis Complete'
                : 'Analyzing Memory Dump...'
              }
            </h2>
            <p className="text-sm text-text-secondary">
              {isComplete
                ? `${currentAnalysis?.total_process_count || 0} processes analyzed • ${currentAnalysis?.hidden_process_count || 0} hidden`
                : 'Running Volatility 3 plugins in parallel'
              }
            </p>
          </div>
        </div>

        {/* Connection indicator */}
        <div className="flex items-center gap-2 text-xs">
          <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-accent-green animate-pulse-slow' : 'bg-accent-red'}`} />
          <span className="text-text-secondary">{isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>

      {/* Alert Banner (when threats found) */}
      {isComplete && hasHidden && (
        <div className="bg-hidden-bg border border-accent-red/30 rounded-card p-4 flex items-center gap-4
          animate-fade-in shadow-glow-red">
          <AlertTriangle size={24} className="text-accent-red shrink-0 animate-glow-pulse" />
          <div className="flex-1">
            <p className="text-accent-red font-bold text-sm">
              {currentAnalysis.hidden_process_count} DKOM-Hidden Process{currentAnalysis.hidden_process_count > 1 ? 'es' : ''} Detected
            </p>
            <p className="text-accent-red/70 text-xs mt-0.5">
              Processes were found in raw memory scan (psscan) but NOT in the OS process list (pslist).
              This is a strong indicator of rootkit activity.
            </p>
          </div>
        </div>
      )}

      {/* Overall Progress */}
      {!isComplete && (
        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-text-secondary">Overall Progress</span>
            <span className="text-sm font-mono font-bold text-text-primary">{overallProgress}%</span>
          </div>
          <div className="w-full h-2 bg-bg-elevated rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-brand to-accent-blue rounded-full transition-all duration-700 ease-out"
              style={{ width: `${overallProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Plugin Stepper */}
      <div className="card">
        <PluginStepper />
      </div>

      {/* Terminal Feed */}
      <div>
        <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
          Live Analysis Feed
        </h3>
        <TerminalFeed />
      </div>

      {/* View Dashboard Button */}
      {isComplete && (
        <div className="flex justify-center pt-4 animate-fade-in">
          <button
            onClick={() => navigate(`/dashboard/${id}`)}
            className="flex items-center gap-3 px-8 py-3 bg-brand text-white font-semibold
              rounded-btn hover:bg-brand/90 transition-all shadow-glow-brand text-base"
            id="view-dashboard-btn"
          >
            View Dashboard
            <ArrowRight size={18} />
          </button>
        </div>
      )}
    </div>
  );
}
