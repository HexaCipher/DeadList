import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import {
  Upload as UploadIcon, FileWarning, HardDrive,
  Shield, Hash, CheckCircle2, AlertCircle, Cpu
} from 'lucide-react';
import toast from 'react-hot-toast';
import { uploadDump } from '../utils/api';
import { formatBytes } from '../utils/scoring';
import useAnalysisStore from '../store/analysisStore';

export default function Upload() {
  const navigate = useNavigate();
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [fileInfo, setFileInfo] = useState(null);
  const [hashes, setHashes] = useState(null);
  const { setCurrentAnalysis, setAnalysisStatus, setUploadProgress, reset } = useAnalysisStore();

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;
    const file = acceptedFiles[0];

    // Reset state
    reset();
    setFileInfo({
      name: file.name,
      size: file.size,
      type: file.type || 'application/octet-stream',
    });

    // Start upload
    setUploading(true);
    setAnalysisStatus('uploading');

    try {
      const response = await uploadDump(file, (pct) => {
        setProgress(pct);
        setUploadProgress(pct);
      });

      const data = response.data;
      setHashes({ md5: data.md5, sha256: data.sha256 });
      setCurrentAnalysis(data);
      setAnalysisStatus('analyzing');

      toast.success('Upload complete — analysis started!');

      // Navigate to analysis page after brief delay
      setTimeout(() => {
        navigate(`/analysis/${data.analysis_id}`);
      }, 1500);
    } catch (err) {
      const message = err.response?.data?.detail || 'Upload failed';
      toast.error(message);
      setAnalysisStatus('failed');
    } finally {
      setUploading(false);
    }
  }, [navigate, reset, setCurrentAnalysis, setAnalysisStatus, setUploadProgress]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    disabled: uploading,
  });

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-56px)] p-8">
      {/* Hero */}
      <div className="text-center mb-10 animate-fade-in">
        <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-accent-red/10 border border-accent-red/20
          flex items-center justify-center shadow-glow-red">
          <Cpu size={36} className="text-accent-red" />
        </div>
        <h1 className="text-3xl font-bold text-text-primary mb-3">
          Memory Forensics Analysis
        </h1>
        <p className="text-text-secondary text-base max-w-lg mx-auto leading-relaxed">
          Upload a RAM dump to detect hidden malware processes, suspicious network connections,
          and injected code that's invisible to Task Manager.
        </p>
      </div>

      {/* Drop Zone */}
      <div
        {...getRootProps()}
        id="upload-dropzone"
        className={`
          w-full max-w-2xl border-2 border-dashed rounded-xl p-12
          text-center cursor-pointer transition-all duration-300
          ${isDragActive
            ? 'dropzone-active border-brand bg-brand/5'
            : uploading
              ? 'border-accent-amber/40 bg-bg-surface'
              : 'border-border-subtle bg-bg-surface hover:border-text-secondary hover:bg-bg-elevated/30'
          }
        `}
      >
        <input {...getInputProps()} />

        {uploading ? (
          /* Upload Progress */
          <div className="space-y-6">
            <div className="w-16 h-24 mx-auto relative">
              {/* RAM Stick Visualization */}
              <div className="w-full h-full border-2 border-accent-amber/40 rounded-md overflow-hidden relative">
                <div
                  className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-accent-amber to-accent-amber/60
                    transition-all duration-500 ease-out"
                  style={{ height: `${progress}%` }}
                />
                <HardDrive size={20} className="absolute inset-0 m-auto text-accent-amber/60 z-10" />
              </div>
            </div>
            <div>
              <p className="text-text-primary font-semibold text-lg">{progress}%</p>
              <p className="text-text-secondary text-sm mt-1">Uploading {fileInfo?.name}...</p>
            </div>
            {/* Progress bar */}
            <div className="w-full max-w-md mx-auto h-2 bg-bg-elevated rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-accent-amber to-brand rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        ) : hashes ? (
          /* Upload Complete — Show Hashes */
          <div className="space-y-4 animate-fade-in">
            <CheckCircle2 size={48} className="mx-auto text-accent-green" />
            <p className="text-accent-green font-semibold text-lg">Upload Complete</p>
            <div className="space-y-2 max-w-md mx-auto">
              <div className="flex items-center gap-2 text-sm">
                <Hash size={14} className="text-text-secondary shrink-0" />
                <span className="text-text-secondary">MD5:</span>
                <code className="font-mono text-xs text-text-primary bg-bg-elevated px-2 py-0.5 rounded truncate">
                  {hashes.md5}
                </code>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Hash size={14} className="text-text-secondary shrink-0" />
                <span className="text-text-secondary">SHA256:</span>
                <code className="font-mono text-xs text-text-primary bg-bg-elevated px-2 py-0.5 rounded truncate">
                  {hashes.sha256}
                </code>
              </div>
            </div>
            <p className="text-text-secondary text-sm mt-4">Redirecting to analysis...</p>
          </div>
        ) : (
          /* Default Drop Zone */
          <div className="space-y-4">
            <div className={`w-16 h-16 mx-auto rounded-xl flex items-center justify-center
              ${isDragActive ? 'bg-brand/20' : 'bg-bg-elevated'} transition-colors`}>
              <UploadIcon size={28} className={`${isDragActive ? 'text-brand' : 'text-text-secondary'} transition-colors`} />
            </div>
            <div>
              <p className="text-text-primary font-semibold text-lg">
                {isDragActive ? 'Drop your memory dump here' : 'Drag & drop a memory dump'}
              </p>
              <p className="text-text-secondary text-sm mt-1">
                or <span className="text-brand hover:underline">browse files</span>
              </p>
            </div>
            <div className="flex items-center justify-center gap-4 text-xs text-text-disabled">
              <span className="flex items-center gap-1">
                <FileWarning size={12} />
                .raw .mem .dmp .vmem .img
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <HardDrive size={12} />
                Max 16GB
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-2xl w-full mt-10">
        {[
          {
            icon: Shield,
            color: 'text-accent-red',
            title: 'DKOM Detection',
            desc: 'Finds processes hidden from Task Manager via Direct Kernel Object Manipulation',
          },
          {
            icon: Cpu,
            color: 'text-accent-amber',
            title: '5 Plugin Analysis',
            desc: 'Runs pslist, psscan, netscan, malfind, and cmdline in parallel',
          },
          {
            icon: AlertCircle,
            color: 'text-accent-green',
            title: 'Threat Scoring',
            desc: '7-criteria suspicion scoring with automatic risk level classification',
          },
        ].map((card, i) => (
          <div key={i} className="card text-center animate-fade-in" style={{ animationDelay: `${i * 100}ms` }}>
            <card.icon size={20} className={`mx-auto mb-2 ${card.color}`} />
            <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1">{card.title}</h3>
            <p className="text-xs text-text-disabled leading-relaxed">{card.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
