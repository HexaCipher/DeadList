import { useMemo } from 'react';
import Tree from 'react-d3-tree';
import { getScoreColor, getStatusColor } from '../utils/scoring';

export default function ProcessTree({ processes = [] }) {
  // Build tree structure from flat process list
  const treeData = useMemo(() => {
    if (processes.length === 0) return null;

    const processMap = {};
    const roots = [];

    // Create node map
    processes.forEach(proc => {
      processMap[proc.pid] = {
        name: `${proc.name} (${proc.pid})`,
        attributes: {
          PID: proc.pid,
          Score: proc.suspicion_score,
          Status: proc.status,
        },
        children: [],
        _data: proc,
      };
    });

    // Build parent-child relationships
    processes.forEach(proc => {
      const node = processMap[proc.pid];
      if (proc.ppid && processMap[proc.ppid]) {
        processMap[proc.ppid].children.push(node);
      } else {
        roots.push(node);
      }
    });

    // If multiple roots, wrap in a virtual root
    if (roots.length === 1) return roots[0];
    return {
      name: 'System',
      children: roots,
      attributes: { PID: 0, Score: 0, Status: 'clean' },
      _data: { status: 'clean', suspicion_score: 0 },
    };
  }, [processes]);

  if (!treeData) {
    return (
      <div className="card flex items-center justify-center h-64 text-text-disabled text-sm">
        No process data available for tree view.
      </div>
    );
  }

  // Custom node rendering
  const renderNode = ({ nodeDatum }) => {
    const procData = nodeDatum._data || {};
    const color = getStatusColor(procData.status || 'clean');
    const score = procData.suspicion_score || 0;

    return (
      <g>
        <circle
          r={score >= 50 ? 12 : score >= 20 ? 10 : 8}
          fill={`${color}30`}
          stroke={color}
          strokeWidth={2}
        />
        <text
          fill="#E6EDF3"
          fontSize={10}
          fontFamily="Inter, sans-serif"
          textAnchor="start"
          x={16}
          y={-4}
        >
          {nodeDatum.name}
        </text>
        {score > 0 && (
          <text
            fill={getScoreColor(score)}
            fontSize={9}
            fontFamily="JetBrains Mono, monospace"
            fontWeight="bold"
            textAnchor="start"
            x={16}
            y={10}
          >
            Score: {score}
          </text>
        )}
      </g>
    );
  };

  return (
    <div className="card p-0 overflow-hidden" style={{ height: '400px' }}>
      <div className="p-4 border-b border-border-subtle">
        <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
          Process Tree
        </span>
      </div>
      <div style={{ width: '100%', height: 'calc(100% - 49px)' }}>
        <Tree
          data={treeData}
          renderCustomNodeElement={renderNode}
          orientation="horizontal"
          pathFunc="step"
          translate={{ x: 100, y: 200 }}
          nodeSize={{ x: 220, y: 50 }}
          separation={{ siblings: 1, nonSiblings: 1.5 }}
          pathClassFunc={() => 'stroke-border-subtle'}
          svgClassName="bg-bg-base"
          styles={{
            links: { stroke: '#30363D', strokeWidth: 1 },
          }}
          zoomable
          draggable
        />
      </div>
    </div>
  );
}
