import { CheckCircle2, Loader2, XCircle, Circle } from 'lucide-react';
import useAnalysisStore from '../store/analysisStore';

const PLUGIN_LABELS = {
  'windows.pslist':  'pslist',
  'windows.psscan':  'psscan',
  'windows.netscan': 'netscan',
  'windows.malfind': 'malfind',
  'windows.cmdline': 'cmdline',
};

const PLUGIN_DESCRIPTIONS = {
  'windows.pslist':  'Process linked list',
  'windows.psscan':  'Raw memory scan',
  'windows.netscan': 'Network connections',
  'windows.malfind': 'Injected code detection',
  'windows.cmdline': 'Command line args',
};

export default function PluginStepper() {
  const pluginStatuses = useAnalysisStore((s) => s.pluginStatuses);
  const plugins = Object.keys(PLUGIN_LABELS);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'complete':
        return <CheckCircle2 size={20} className="text-accent-green" />;
      case 'running':
        return <Loader2 size={20} className="text-accent-blue animate-spin" />;
      case 'error':
        return <XCircle size={20} className="text-accent-red" />;
      default:
        return <Circle size={20} className="text-text-disabled" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'complete': return 'border-accent-green bg-accent-green/10';
      case 'running':  return 'border-accent-blue bg-accent-blue/10 shadow-glow-blue';
      case 'error':    return 'border-accent-red bg-accent-red/10';
      default:         return 'border-border-subtle bg-bg-surface';
    }
  };

  const completedCount = plugins.filter(p => pluginStatuses[p] === 'complete').length;

  return (
    <div className="w-full">
      {/* Progress bar */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm text-text-secondary">Plugin Execution</span>
        <span className="text-sm font-mono text-text-primary">{completedCount}/{plugins.length}</span>
      </div>

      {/* Stepper */}
      <div className="flex items-start gap-0">
        {plugins.map((plugin, index) => {
          const status = pluginStatuses[plugin];
          return (
            <div key={plugin} className="flex items-start flex-1">
              {/* Step */}
              <div className="flex flex-col items-center flex-1">
                {/* Icon */}
                <div className={`w-10 h-10 rounded-full border-2 flex items-center justify-center
                  transition-all duration-500 ${getStatusColor(status)}`}>
                  {getStatusIcon(status)}
                </div>

                {/* Label */}
                <div className="mt-2 text-center">
                  <p className={`text-xs font-semibold uppercase tracking-wider
                    ${status === 'complete' ? 'text-accent-green' :
                      status === 'running' ? 'text-accent-blue' :
                      status === 'error' ? 'text-accent-red' :
                      'text-text-disabled'}`}>
                    {PLUGIN_LABELS[plugin]}
                  </p>
                  <p className="text-[10px] text-text-disabled mt-0.5 hidden md:block">
                    {PLUGIN_DESCRIPTIONS[plugin]}
                  </p>
                </div>
              </div>

              {/* Connector line */}
              {index < plugins.length - 1 && (
                <div className="flex items-center h-10 px-1 flex-shrink-0">
                  <div className={`h-0.5 w-full min-w-[20px] transition-colors duration-500
                    ${status === 'complete' ? 'bg-accent-green' : 'bg-border-subtle'}`}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
