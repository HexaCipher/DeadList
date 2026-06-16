import { useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { CheckCircle2, Loader2, XCircle, Circle, AlertTriangle } from 'lucide-react';
import useAnalysisStore from '../store/analysisStore';

export default function TerminalFeed() {
  const wsMessages = useAnalysisStore((s) => s.wsMessages);
  const feedRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [wsMessages]);

  const getMessageStyle = (msg) => {
    if (msg.event === 'anomaly_found') return 'terminal-alert';
    if (msg.event === 'plugin_error') return 'terminal-alert';
    if (msg.event === 'analysis_complete') return 'text-accent-green font-bold';
    return 'terminal-text';
  };

  const getMessageIcon = (msg) => {
    switch (msg.event) {
      case 'plugin_started':    return '🔄';
      case 'plugin_complete':   return '✅';
      case 'plugin_error':      return '❌';
      case 'anomaly_found':     return '🚨';
      case 'analysis_complete': return '🎯';
      case 'progress':          return '▸';
      case 'connected':         return '🔗';
      default:                  return '▸';
    }
  };

  const formatMessage = (msg) => {
    switch (msg.event) {
      case 'plugin_started':
        return `Running ${msg.plugin}...`;
      case 'plugin_complete':
        return `${msg.plugin} complete — ${msg.count || 0} results found`;
      case 'plugin_error':
        return `${msg.plugin} FAILED: ${msg.error}`;
      case 'anomaly_found':
        return `ALERT: ${msg.type === 'hidden_process' ? 'Hidden process' : 'Anomaly'} detected — PID ${msg.pid} (${msg.name})`;
      case 'analysis_complete':
        return `Analysis complete — Risk: ${msg.risk_level?.toUpperCase()} | ${msg.hidden_count} hidden process(es)`;
      case 'progress':
        return msg.message;
      case 'connected':
        return msg.message || 'Connected to analysis stream';
      default:
        return JSON.stringify(msg);
    }
  };

  const formatTime = (ts) => {
    const date = new Date(ts);
    return date.toLocaleTimeString('en-US', { hour12: false });
  };

  return (
    <div
      ref={feedRef}
      className="bg-bg-base border border-border-subtle rounded-card overflow-y-auto font-mono text-[13px] p-4"
      style={{ maxHeight: '320px' }}
    >
      {wsMessages.length === 0 ? (
        <div className="text-text-disabled text-center py-8">
          Waiting for analysis events...
        </div>
      ) : (
        <div className="space-y-1">
          {wsMessages.map((msg, i) => (
            <div key={i} className={`flex gap-2 ${getMessageStyle(msg)}`}>
              <span className="text-text-secondary shrink-0">
                [{formatTime(msg._timestamp || msg.timestamp)}]
              </span>
              <span>{getMessageIcon(msg)}</span>
              <span className="break-all">{formatMessage(msg)}</span>
              {msg.event === 'anomaly_found' && (
                <span className="animate-blink text-accent-red ml-1">●</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
