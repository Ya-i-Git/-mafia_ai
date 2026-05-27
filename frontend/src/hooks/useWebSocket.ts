import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuthStore } from '../stores/authStore';
import { useGameStore } from '../stores/gameStore';
import { useChatStore } from '../stores/chatStore';

export function useWebSocket(gameId: string) {
  const { username } = useAuthStore();
  const setGameState = useGameStore((state) => state.setGameState);
  const setCurrentRole = useGameStore((state) => state.setCurrentRole);   // ← добавим в gameStore
  const addMessage = useChatStore((state) => state.addMessage);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!username || !gameId) return;
    const wsUrl = `/ws/${gameId}?username=${encodeURIComponent(username)}`;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const fullUrl = `${protocol}//${window.location.host}${wsUrl}`;
    const ws = new WebSocket(fullUrl);
    wsRef.current = ws;
    ws.onopen = () => setConnected(true);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'game_state') setGameState(data.state);
        else if (data.type === 'system') {
          // Проверяем, не содержит ли сообщение информацию о роли
          const roleMatch = data.text.match(/Ваша роль: (\w+)/);
          if (roleMatch) {
            setCurrentRole(roleMatch[1]);
          }
          addMessage('common', { text: data.text, username: 'Ведущий', timestamp: new Date() });
        } else if (data.type === 'chat') {
          const tab = data.mafia_chat ? 'night' : 'common';
          addMessage(tab, { text: data.text, username: data.from, timestamp: new Date() });
        }
      } catch (e) { console.error(e); }
    };
    ws.onclose = () => setConnected(false);
    ws.onerror = (error) => console.error(error);
    return () => { if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) ws.close(); };
  }, [username, gameId, setGameState, setCurrentRole, addMessage]);

  const sendMessage = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) wsRef.current.send(JSON.stringify(message));
    else console.warn('WebSocket is not connected');
  }, []);

  return { connected, sendMessage };
}