import { useEffect, useRef, useState } from 'react';

export function useWebSocket(token: string | null, gameId: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!token) return;
    
    // ← ЗАМЕНИТЕ на прямую ссылку
    const wsUrl = 'ws://localhost:8000';
    const ws = new WebSocket(`${wsUrl}/ws/${token}`);
    wsRef.current = ws;
    
    ws.onopen = () => {
      setIsConnected(true);
      ws.send(JSON.stringify({ type: 'join', game_id: parseInt(gameId) }));
    };
    
    ws.onmessage = (e) => {
      setLastMessage(e.data);
    };
    
    ws.onclose = () => {
      setIsConnected(false);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [token, gameId]);

  const sendMessage = (data: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(data);
    } else {
      console.warn('WebSocket is not connected');
    }
  };

  return { isConnected, lastMessage, sendMessage };
}