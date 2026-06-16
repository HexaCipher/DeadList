import { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';
import Upload from './pages/Upload';
import Analysis from './pages/Analysis';
import Dashboard from './pages/Dashboard';
import HistoryPage from './pages/History';

export default function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="flex min-h-screen bg-bg-base">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      <div
        className={`flex-1 flex flex-col transition-all duration-300
          ${sidebarCollapsed ? 'ml-16' : 'ml-60'}`}
      >
        <Header />

        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Upload />} />
            <Route path="/analysis/:id" element={<Analysis />} />
            <Route path="/dashboard/:id" element={<Dashboard />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
