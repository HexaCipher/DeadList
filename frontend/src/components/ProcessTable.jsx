import { useState, useMemo } from 'react';
import { Search, Filter, ArrowUpDown, ChevronUp, ChevronDown } from 'lucide-react';
import { getScoreColor, getStatusBadgeClass, getScoreBarWidth } from '../utils/scoring';
import useAnalysisStore from '../store/analysisStore';

export default function ProcessTable({ processes = [] }) {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortField, setSortField] = useState('suspicion_score');
  const [sortOrder, setSortOrder] = useState('desc');
  const setSelectedProcess = useAnalysisStore((s) => s.setSelectedProcess);

  // Filter and sort
  const filtered = useMemo(() => {
    let result = [...processes];

    // Search
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(p =>
        p.name?.toLowerCase().includes(q) ||
        String(p.pid).includes(q)
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      result = result.filter(p => p.status === statusFilter);
    }

    // Sort
    result.sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];

      if (typeof aVal === 'string') aVal = aVal.toLowerCase();
      if (typeof bVal === 'string') bVal = bVal.toLowerCase();

      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return result;
  }, [processes, search, statusFilter, sortField, sortOrder]);

  const toggleSort = (field) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const SortIcon = ({ field }) => {
    if (sortField !== field) return <ArrowUpDown size={12} className="text-text-disabled" />;
    return sortOrder === 'asc'
      ? <ChevronUp size={12} className="text-accent-blue" />
      : <ChevronDown size={12} className="text-accent-blue" />;
  };

  const getRowClass = (status) => {
    switch (status) {
      case 'hidden': return 'process-row-hidden';
      case 'suspicious': return 'process-row-suspicious';
      case 'anomalous': return 'process-row-anomalous';
      default: return 'process-row-clean';
    }
  };

  return (
    <div className="card p-0 overflow-hidden">
      {/* Filter Bar */}
      <div className="flex items-center gap-3 p-4 border-b border-border-subtle">
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-disabled" />
          <input
            type="text"
            placeholder="Search by name or PID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-bg-elevated border border-border-subtle rounded-btn
              text-sm text-text-primary placeholder:text-text-disabled
              focus:outline-none focus:border-brand focus:ring-1 focus:ring-brand/30"
            id="process-search"
          />
        </div>

        <div className="flex items-center gap-1">
          <Filter size={14} className="text-text-disabled" />
          {['all', 'hidden', 'suspicious', 'clean'].map(status => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-2.5 py-1 text-xs font-medium rounded-badge transition-colors
                ${statusFilter === status
                  ? 'bg-brand text-white'
                  : 'bg-bg-elevated text-text-secondary hover:text-text-primary'
                }`}
            >
              {status === 'all' ? 'All' : status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>

        <span className="text-xs text-text-disabled ml-auto">
          {filtered.length} of {processes.length} processes
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border-subtle">
              {[
                { field: 'pid', label: 'PID', width: 'w-20' },
                { field: 'name', label: 'PROCESS NAME', width: 'flex-1' },
                { field: 'ppid', label: 'PPID', width: 'w-20' },
                { field: 'status', label: 'STATUS', width: 'w-28' },
                { field: 'suspicion_score', label: 'SCORE', width: 'w-32' },
                { field: 'cmdline', label: 'CMDLINE', width: 'w-48' },
              ].map(col => (
                <th
                  key={col.field}
                  onClick={() => toggleSort(col.field)}
                  className={`px-4 py-3 text-left text-[11px] font-semibold text-text-secondary
                    uppercase tracking-wider cursor-pointer hover:text-text-primary transition-colors ${col.width}`}
                >
                  <div className="flex items-center gap-1.5">
                    {col.label}
                    <SortIcon field={col.field} />
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((proc) => (
              <tr
                key={`${proc.pid}-${proc.name}`}
                onClick={() => setSelectedProcess(proc)}
                className={`table-row-hover ${getRowClass(proc.status)} border-b border-border-subtle/50`}
              >
                <td className="px-4 py-3 font-mono text-sm text-text-primary">{proc.pid}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-text-primary">{proc.name}</span>
                    {proc.is_hidden && (
                      <span className="text-[9px] font-bold text-accent-red bg-accent-red/10 px-1.5 py-0.5 rounded">
                        HIDDEN
                      </span>
                    )}
                    {proc.has_injected_code && (
                      <span className="text-[9px] font-bold text-accent-amber bg-accent-amber/10 px-1.5 py-0.5 rounded">
                        INJECTED
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 font-mono text-sm text-text-secondary">{proc.ppid ?? '—'}</td>
                <td className="px-4 py-3">
                  <span className={getStatusBadgeClass(proc.status)}>
                    {proc.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span
                      className="font-mono text-sm font-bold"
                      style={{ color: getScoreColor(proc.suspicion_score) }}
                    >
                      {proc.suspicion_score}
                    </span>
                    <div className="w-16 h-1.5 bg-bg-elevated rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{
                          width: getScoreBarWidth(proc.suspicion_score),
                          backgroundColor: getScoreColor(proc.suspicion_score),
                        }}
                      />
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className="font-mono text-xs text-text-secondary truncate block max-w-[200px]"
                    title={proc.cmdline || '(empty)'}
                  >
                    {proc.cmdline || <span className="text-accent-red italic">empty</span>}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-12 text-text-disabled text-sm">
          No processes match your filters.
        </div>
      )}
    </div>
  );
}
