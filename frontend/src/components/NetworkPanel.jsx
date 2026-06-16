import { useMemo } from 'react';
import { Globe, AlertTriangle, MapPin } from 'lucide-react';
import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
  Line,
} from 'react-simple-maps';

const GEO_URL = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

export default function NetworkPanel({ connections = [] }) {
  // Extract unique markers with lat/lon
  const markers = useMemo(() => {
    const seen = new Set();
    return connections
      .filter(c => c.lat && c.lon && c.remote_addr)
      .filter(c => {
        const key = `${c.lat}-${c.lon}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .map(c => ({
        name: `${c.city || ''}, ${c.country || ''}`.replace(/^, /, ''),
        coordinates: [c.lon, c.lat],
        suspicious: c.is_suspicious_port,
        ip: c.remote_addr,
        port: c.remote_port,
      }));
  }, [connections]);

  const suspiciousCount = connections.filter(c => c.is_suspicious_port).length;

  return (
    <div className="space-y-4">
      {/* World Map */}
      {markers.length > 0 && (
        <div className="card p-0 overflow-hidden">
          <div className="p-4 border-b border-border-subtle flex items-center gap-2">
            <Globe size={16} className="text-accent-blue" />
            <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
              Connection Map
            </span>
            <span className="text-xs text-text-disabled ml-auto">
              {markers.length} unique location{markers.length !== 1 ? 's' : ''}
            </span>
          </div>
          <div className="bg-bg-base p-2" style={{ height: '280px' }}>
            <ComposableMap
              projection="geoMercator"
              projectionConfig={{ scale: 120, center: [20, 20] }}
              style={{ width: '100%', height: '100%' }}
            >
              <Geographies geography={GEO_URL}>
                {({ geographies }) =>
                  geographies.map((geo) => (
                    <Geography
                      key={geo.rpiSmallerId || geo.properties.name}
                      geography={geo}
                      fill="#161B22"
                      stroke="#30363D"
                      strokeWidth={0.5}
                      style={{
                        default: { outline: 'none' },
                        hover: { fill: '#21262D', outline: 'none' },
                        pressed: { outline: 'none' },
                      }}
                    />
                  ))
                }
              </Geographies>
              {markers.map((marker, i) => (
                <Marker key={i} coordinates={marker.coordinates}>
                  <circle
                    r={marker.suspicious ? 6 : 4}
                    fill={marker.suspicious ? '#F85149' : '#58A6FF'}
                    opacity={0.8}
                    stroke={marker.suspicious ? '#F85149' : '#58A6FF'}
                    strokeWidth={marker.suspicious ? 3 : 1}
                    strokeOpacity={0.3}
                  />
                  <text
                    textAnchor="middle"
                    y={-10}
                    style={{ fontSize: '8px', fill: '#8B949E', fontFamily: 'Inter' }}
                  >
                    {marker.name}
                  </text>
                </Marker>
              ))}
            </ComposableMap>
          </div>
        </div>
      )}

      {/* Connections Table */}
      <div className="card p-0 overflow-hidden">
        <div className="p-4 border-b border-border-subtle flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
              Network Connections
            </span>
            <span className="text-xs text-text-disabled">({connections.length})</span>
          </div>
          {suspiciousCount > 0 && (
            <div className="flex items-center gap-1.5 text-xs text-accent-red">
              <AlertTriangle size={12} />
              {suspiciousCount} suspicious
            </div>
          )}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border-subtle">
                {['PID', 'Process', 'Local', 'Remote', 'State', 'Protocol', 'Location'].map(h => (
                  <th key={h} className="px-4 py-2.5 text-left text-[11px] font-semibold text-text-secondary uppercase tracking-wider">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {connections.map((conn, i) => (
                <tr
                  key={i}
                  className={`table-row-hover border-b border-border-subtle/50
                    ${conn.is_suspicious_port ? 'process-row-hidden' : ''}`}
                >
                  <td className="px-4 py-2.5 font-mono text-xs text-text-primary">{conn.pid}</td>
                  <td className="px-4 py-2.5 text-xs text-text-primary">{conn.process_name || '—'}</td>
                  <td className="px-4 py-2.5 font-mono text-xs text-text-secondary">
                    {conn.local_addr}:{conn.local_port}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs">
                    <span className={conn.is_suspicious_port ? 'text-accent-red font-bold' : 'text-text-secondary'}>
                      {conn.remote_addr || '*'}:{conn.remote_port || '*'}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-xs text-text-secondary">{conn.state || '—'}</td>
                  <td className="px-4 py-2.5 text-xs text-text-disabled">{conn.protocol}</td>
                  <td className="px-4 py-2.5 text-xs text-text-disabled">
                    {conn.country ? (
                      <span className="flex items-center gap-1">
                        <MapPin size={10} />
                        {conn.city && `${conn.city}, `}{conn.country}
                      </span>
                    ) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {connections.length === 0 && (
          <div className="text-center py-8 text-text-disabled text-sm">
            No network connections found.
          </div>
        )}
      </div>
    </div>
  );
}
