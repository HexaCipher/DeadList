/**
 * DeadList Scoring Utilities
 * Score → color/label/badge helpers for the frontend.
 */

export const getScoreColor = (score) => {
  if (score >= 80) return '#F85149';  // Critical red
  if (score >= 50) return '#F85149';  // Red
  if (score >= 30) return '#D29922';  // Amber
  if (score >= 10) return '#58A6FF';  // Blue
  return '#3FB950';                   // Green
};

export const getScoreLabel = (score) => {
  if (score >= 80) return 'CRITICAL';
  if (score >= 50) return 'HIGH';
  if (score >= 30) return 'MEDIUM';
  if (score >= 10) return 'LOW';
  return 'CLEAN';
};

export const getStatusColor = (status) => {
  switch (status) {
    case 'hidden':     return '#F85149';
    case 'suspicious': return '#D29922';
    case 'anomalous':  return '#58A6FF';
    case 'clean':      return '#3FB950';
    default:           return '#8B949E';
  }
};

export const getStatusBadgeClass = (status) => {
  switch (status) {
    case 'hidden':     return 'badge-critical';
    case 'suspicious': return 'badge-suspicious';
    case 'anomalous':  return 'badge-anomalous';
    case 'clean':      return 'badge-clean';
    default:           return 'badge-clean';
  }
};

export const getRiskLevelColor = (level) => {
  switch (level) {
    case 'critical': return '#F85149';
    case 'high':     return '#F85149';
    case 'medium':   return '#D29922';
    case 'low':      return '#58A6FF';
    case 'clean':    return '#3FB950';
    default:         return '#8B949E';
  }
};

export const getRiskLevelBg = (level) => {
  switch (level) {
    case 'critical': return 'bg-hidden-bg';
    case 'high':     return 'bg-hidden-bg';
    case 'medium':   return 'bg-suspicious-bg';
    case 'low':      return 'bg-anomalous-bg';
    case 'clean':    return 'bg-clean-bg';
    default:         return 'bg-bg-surface';
  }
};

export const getScoreBarWidth = (score) => `${Math.min(score, 100)}%`;

export const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
};

export const formatTimestamp = (ts) => {
  if (!ts) return 'N/A';
  const date = new Date(ts);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};
