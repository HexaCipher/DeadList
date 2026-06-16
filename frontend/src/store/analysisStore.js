import { create } from 'zustand';

const useAnalysisStore = create((set, get) => ({
  // ─── Analysis State ────────────────────────────────────
  currentAnalysis: null,
  analysisStatus: 'idle', // idle / uploading / analyzing / complete / failed
  uploadProgress: 0,

  // ─── Plugin Progress ───────────────────────────────────
  pluginStatuses: {
    'windows.pslist':  'pending',
    'windows.psscan':  'pending',
    'windows.netscan': 'pending',
    'windows.malfind': 'pending',
    'windows.cmdline': 'pending',
  },
  overallProgress: 0,

  // ─── Data ─────────────────────────────────────────────
  processes: [],
  connections: [],
  memoryRegions: [],
  
  // ─── UI State ──────────────────────────────────────────
  selectedProcess: null,
  drawerOpen: false,
  wsMessages: [],

  // ─── Actions ───────────────────────────────────────────
  setCurrentAnalysis: (analysis) => set({ currentAnalysis: analysis }),
  
  setAnalysisStatus: (status) => set({ analysisStatus: status }),
  
  setUploadProgress: (progress) => set({ uploadProgress: progress }),

  updatePluginStatus: (plugin, status) => set((state) => ({
    pluginStatuses: {
      ...state.pluginStatuses,
      [plugin]: status,
    },
  })),

  setOverallProgress: (percent) => set({ overallProgress: percent }),

  setProcesses: (processes) => set({ processes }),
  
  setConnections: (connections) => set({ connections }),
  
  setMemoryRegions: (regions) => set({ memoryRegions: regions }),

  setSelectedProcess: (process) => set({
    selectedProcess: process,
    drawerOpen: process !== null,
  }),

  closeDrawer: () => set({
    selectedProcess: null,
    drawerOpen: false,
  }),

  addWSMessage: (message) => set((state) => ({
    wsMessages: [...state.wsMessages, {
      ...message,
      _timestamp: new Date().toISOString(),
    }],
  })),

  // Handle incoming WebSocket events
  handleWSEvent: (data) => {
    const { addWSMessage, updatePluginStatus, setOverallProgress, setAnalysisStatus, setCurrentAnalysis } = get();
    
    addWSMessage(data);

    switch (data.event) {
      case 'plugin_started':
        updatePluginStatus(data.plugin, 'running');
        break;

      case 'plugin_complete':
        updatePluginStatus(data.plugin, 'complete');
        break;

      case 'plugin_error':
        updatePluginStatus(data.plugin, 'error');
        break;

      case 'progress':
        setOverallProgress(data.percent);
        break;

      case 'analysis_complete':
        setAnalysisStatus('complete');
        set((state) => ({
          currentAnalysis: {
            ...state.currentAnalysis,
            status: 'complete',
            risk_level: data.risk_level,
            hidden_process_count: data.hidden_count,
            total_process_count: data.total_processes,
          },
        }));
        break;

      case 'anomaly_found':
        // Could trigger toast notifications
        break;

      default:
        break;
    }
  },

  // Reset store for new analysis
  reset: () => set({
    currentAnalysis: null,
    analysisStatus: 'idle',
    uploadProgress: 0,
    pluginStatuses: {
      'windows.pslist':  'pending',
      'windows.psscan':  'pending',
      'windows.netscan': 'pending',
      'windows.malfind': 'pending',
      'windows.cmdline': 'pending',
    },
    overallProgress: 0,
    processes: [],
    connections: [],
    memoryRegions: [],
    selectedProcess: null,
    drawerOpen: false,
    wsMessages: [],
  }),
}));

export default useAnalysisStore;
