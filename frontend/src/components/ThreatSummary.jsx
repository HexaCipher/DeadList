import { useEffect, useState } from 'react';
import { EyeOff, Wifi, ShieldCheck, AlertTriangle, Bug } from 'lucide-react';
import { getRiskLevelColor } from '../utils/scoring';
import useAnalysisStore from '../store/analysisStore';

export default function ThreatSummary({ analysis }) {
  const [animated, setAnimated] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setAnimated(true), 100);
    return () => clearTimeout(timer);
  }, []);

  const processes = useAnalysisStore((s) => s.processes);
  const suspiciousCount = processes.filter(p => p.suspicion_score >= 30).length;

  const cards = [
    {
      icon: EyeOff,
      label: 'HIDDEN PROCESSES',
      value: analysis?.hidden_process_count || 0,
      color: '#F85149',
      bgColor: 'bg-hidden-bg',
      glow: analysis?.hidden_process_count > 0 ? 'shadow-glow-red' : '',
      description: 'DKOM-hidden from Task Manager',
    },
    {
      icon: Bug,
      label: 'SUSPICIOUS PROCESSES',
      value: suspiciousCount,
      color: '#D29922',
      bgColor: 'bg-suspicious-bg',
      glow: suspiciousCount > 0 ? 'shadow-glow-amber' : '',
      description: 'Processes with score ≥ 30',
    },
    {
      icon: ShieldCheck,
      label: 'TOTAL PROCESSES',
      value: analysis?.total_process_count || 0,
      color: '#3FB950',
      bgColor: 'bg-clean-bg',
      glow: '',
      description: 'Discovered in memory dump',
    },
    {
      icon: AlertTriangle,
      label: 'RISK LEVEL',
      value: (analysis?.risk_level || 'unknown').toUpperCase(),
      color: getRiskLevelColor(analysis?.risk_level),
      bgColor: 'bg-bg-surface',
      glow: analysis?.risk_level === 'critical' ? 'shadow-glow-red animate-glow-pulse' : '',
      description: 'Overall threat assessment',
      isText: true,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, i) => (
        <div
          key={card.label}
          className={`card ${card.glow} animate-fade-in border-border-subtle relative overflow-hidden`}
          style={{ animationDelay: `${i * 80}ms` }}
        >
          {/* Icon */}
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] font-semibold text-text-secondary uppercase tracking-widest">
              {card.label}
            </span>
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ backgroundColor: `${card.color}15` }}
            >
              <card.icon size={16} style={{ color: card.color }} />
            </div>
          </div>

          {/* Value */}
          <div className="flex items-end gap-2">
            {card.isText ? (
              <span
                className="text-2xl font-bold font-mono tracking-tight"
                style={{ color: card.color }}
              >
                {animated ? card.value : '—'}
              </span>
            ) : (
              <span
                className="text-3xl font-bold font-mono tabular-nums"
                style={{ color: card.color }}
              >
                {animated ? card.value : 0}
              </span>
            )}
          </div>

          {/* Description */}
          <p className="text-[11px] text-text-disabled mt-1">{card.description}</p>

          {/* Subtle accent line at bottom */}
          <div
            className="absolute bottom-0 left-0 right-0 h-0.5"
            style={{ backgroundColor: card.color, opacity: 0.3 }}
          />
        </div>
      ))}
    </div>
  );
}
