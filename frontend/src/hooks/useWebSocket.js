import { useEffect, useRef, useCallback, useState } from 'react';
import useAnalysisStore from '../store/analysisStore';

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

/**
 * Custom hook for WebSocket connection to the analysis stream.
 * Handles auto-reconnect with exponential backoff.
 */
export default function useWebSocket(analysisId) {
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const [isConnected, setIsConnected] = useState(false);
  const handleWSEvent = useAnalysisStore((state) => state.handleWSEvent);

  const connect = useCallback(() => {
    if (!analysisId) return;

    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    const ws = new WebSocket(`${WS_BASE_URL}/ws/${analysisId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log(`[WS] Connected to analysis ${analysisId}`);
      setIsConnected(true);
      reconnectAttempts.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWSEvent(data);
      } catch (err) {
        console.error('[WS] Failed to parse message:', err);
      }
    };

    ws.onclose = (event) => {
      console.log(`[WS] Disconnected (code: ${event.code})`);
      setIsConnected(false);

      // Auto-reconnect with exponential backoff (max 5 attempts)
      if (reconnectAttempts.current < 5 && event.code !== 1000) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000);
        console.log(`[WS] Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current + 1})`);
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttempts.current += 1;
          connect();
        }, delay);
      }
    };

    ws.onerror = (error) => {
      console.error('[WS] Error:', error);
    };
  }, [analysisId, handleWSEvent]);

  // Send message to server
  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close(1000); // Normal closure
      }
    };
  }, [connect]);

  // Periodic ping to keep connection alive
  useEffect(() => {
    const pingInterval = setInterval(() => {
      send({ type: 'ping' });
    }, 30000);

    return () => clearInterval(pingInterval);
  }, [send]);

  return { isConnected, send };
}
