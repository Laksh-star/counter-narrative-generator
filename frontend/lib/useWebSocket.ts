/**
 * WebSocket hook for streaming query progress
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { apiClient, ProgressUpdate } from './api';

export interface UseWebSocketResult {
  sendMessage: (message: any) => void;
  lastMessage: ProgressUpdate | null;
  readyState: number;
  connect: () => void;
  disconnect: () => void;
  isConnected: () => boolean;
}

export const useWebSocket = (onMessage?: (update: ProgressUpdate) => void): UseWebSocketResult => {
  const [lastMessage, setLastMessage] = useState<ProgressUpdate | null>(null);
  const [readyState, setReadyState] = useState<number>(WebSocket.CLOSED);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = apiClient.getWebSocketUrl();
    console.log('Attempting WebSocket connection to:', wsUrl);

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected successfully');
      setReadyState(WebSocket.OPEN);
    };

    ws.onmessage = (event) => {
      try {
        const update: ProgressUpdate = JSON.parse(event.data);
        console.log('WebSocket message received:', update);
        setLastMessage(update);
        if (onMessage) {
          onMessage(update);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setReadyState(WebSocket.CLOSED);
    };

    ws.onclose = (event) => {
      console.log('WebSocket disconnected. Code:', event.code, 'Reason:', event.reason);
      setReadyState(WebSocket.CLOSED);
    };

    wsRef.current = ws;
  }, [onMessage]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  }, []);

  const isConnected = useCallback(() => {
    return wsRef.current?.readyState === WebSocket.OPEN;
  }, []);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    sendMessage,
    lastMessage,
    readyState,
    connect,
    disconnect,
    isConnected,
  };
};
