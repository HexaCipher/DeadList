import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  Skull, Upload, Activity, LayoutDashboard,
  History, Settings, ChevronLeft, ChevronRight,
  Shield, Wifi, WifiOff
} from 'lucide-react';

export default function Sidebar({ collapsed, onToggle }) {
  const location = useLocation();

  const navItems = [
    { to: '/',         icon: Upload,          label: 'Upload',    section: 'ANALYSIS' },
    { to: '/history',  icon: History,         label: 'History',   section: 'ANALYSIS' },
  ];

  // Group items by section
  const sections = {};
  navItems.forEach(item => {
    if (!sections[item.section]) sections[item.section] = [];
    sections[item.section].push(item);
  });

  return (
    <aside
      className={`fixed left-0 top-0 h-screen bg-bg-surface border-r border-border-subtle
        flex flex-col transition-all duration-300 z-50
        ${collapsed ? 'w-16' : 'w-60'}`}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 h-14 border-b border-border-subtle shrink-0">
        <div className="w-8 h-8 rounded-lg bg-accent-red/20 flex items-center justify-center shrink-0">
          <Skull size={18} className="text-accent-red" />
        </div>
        {!collapsed && (
          <div className="overflow-hidden">
            <h1 className="text-base font-bold text-text-primary tracking-tight">DeadList</h1>
            <p className="text-[10px] text-text-secondary leading-none truncate">Memory Forensics</p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-2 overflow-y-auto">
        {Object.entries(sections).map(([section, items]) => (
          <div key={section} className="mb-4">
            {!collapsed && (
              <div className="px-3 mb-2 text-[10px] font-semibold text-text-secondary uppercase tracking-widest">
                {section}
              </div>
            )}
            <ul className="space-y-1">
              {items.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.to === '/'}
                    className={({ isActive }) => `
                      flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium
                      transition-all duration-150 group relative
                      ${isActive
                        ? 'bg-bg-elevated text-text-primary border-l-2 border-brand'
                        : 'text-text-secondary hover:text-text-primary hover:bg-bg-elevated/50 border-l-2 border-transparent'
                      }
                    `}
                  >
                    <item.icon size={18} className="shrink-0" />
                    {!collapsed && <span>{item.label}</span>}
                    {collapsed && (
                      <div className="absolute left-full ml-2 px-2 py-1 bg-bg-elevated text-text-primary text-xs
                        rounded-md opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none
                        whitespace-nowrap shadow-lg border border-border-subtle z-50">
                        {item.label}
                      </div>
                    )}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      {/* Collapse Toggle */}
      <button
        onClick={onToggle}
        className="flex items-center justify-center h-10 border-t border-border-subtle
          text-text-secondary hover:text-text-primary transition-colors"
        title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>
    </aside>
  );
}
