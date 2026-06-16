import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Network, TreePine, Table2 } from 'lucide-react';
import useAnalysisStore from '../store/analysisStore';
import { getAnalysis } from '../utils/api';
import ThreatSummary from '../components/ThreatSummary';
import ProcessTable from '../components/ProcessTable';
import ProcessDrawer from '../components/ProcessDrawer';
import NetworkPanel from '../components/NetworkPanel';
import ProcessTree from '../components/ProcessTree';

export default function Dashboard() {
  const { id } = useParams();
  const { currentAnalysis, setCurrentAnalysis, setProcesses, setConnections, setMemoryRegions } = useAnalysisStore();
  const processes = useAnalysisStore((s) => s.processes);
  const connections = useAnalysisStore((s) => s.connections);
  const [activeTab, setActiveTab] = useState('table');
  const [loading, setLoading] = useState(false);

  // Fetch analysis data
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const res = await getAnalysis(id);
        const data = res.data;

        setCurrentAnalysis(data);
        setProcesses(data.processes || []);
        setConnections(data.connections || []);
        setMemoryRegions(data.memory_regions || []);
      } catch (err) {
        console.error('Failed to fetch analysis:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id, setCurrentAnalysis, setProcesses, setConnections, setMemoryRegions]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-brand border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-text-secondary text-sm">Loading analysis results...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Threat Summary Cards */}
      <ThreatSummary analysis={currentAnalysis} />

      {/* Tab Navigation */}
      <div className="flex items-center gap-1 border-b border-border-subtle">
        {[
          { id: 'table', icon: Table2, label: 'Process Table' },
          { id: 'tree', icon: TreePine, label: 'Process Tree' },
          { id: 'network', icon: Network, label: 'Network' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium
              border-b-2 transition-colors -mb-px
              ${activeTab === tab.id
                ? 'border-brand text-text-primary'
                : 'border-transparent text-text-secondary hover:text-text-primary'
              }`}
          >
            <tab.icon size={15} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="animate-fade-in">
        {activeTab === 'table' && <ProcessTable processes={processes} />}
        {activeTab === 'tree' && <ProcessTree processes={processes} />}
        {activeTab === 'network' && <NetworkPanel connections={connections} />}
      </div>

      {/* Process Detail Drawer */}
      <ProcessDrawer />
    </div>
  );
}
