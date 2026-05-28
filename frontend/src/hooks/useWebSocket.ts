import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuthStore } from '../stores/authStore';
import { useGameStore } from '../stores/gameStore';
import { useChatStore } from '../stores/chatStore';

export function useWebSocket(gameId: string) {
  const { username } = useAuthStore();
  const setGameState = useGameStore((state) => state.setGameState);
  const setCurrentRole = useGameStore((state) => state.setCurrentRole);
  const addSheriffCheck = useGameStore((state) => state.addSheriffCheck);
  const addDonCheck = useGameStore((state) => state.addDonCheck);
  const setMafiaTeam = useGameStore((state) => state.setMafiaTeam);
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
    ws.onclose = () => setConnected(false);
    ws.onerror = (error) => console.error(error);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'game_state') {
          setGameState(data.state);
        } else if (data.type === 'role_assigned') {
          setCurrentRole(data.role);
        } else if (data.type === 'mafia_team') {
          setMafiaTeam(data.members, data.don);
        } else if (data.type === 'system') {
          const sheriffMatch = data.text.match(/Проверка (.+?): роль (мафия|мирный)/);
          if (sheriffMatch) {
            const targetName = sheriffMatch[1];
            const role = sheriffMatch[2];
            const targetPlayer = useGameStore.getState().gameState?.players?.find(p => p.username === targetName);
            if (targetPlayer) {
              addSheriffCheck(targetPlayer.id, role);
            }
          }
          const donMatch = data.text.match(/Проверка (.+?): (шериф|не шериф)/);
          if (donMatch) {
            const targetName = donMatch[1];
            const isSheriff = donMatch[2] === 'шериф';
            const targetPlayer = useGameStore.getState().gameState?.players?.find(p => p.username === targetName);
            if (targetPlayer) {
              addDonCheck(targetPlayer.id, isSheriff);
            }
          }
          addMessage('common', { text: data.text, username: 'Ведущий', timestamp: new Date() });
        } else if (data.type === 'chat') {
          if (data.from !== username) {
            const tab = data.mafia_chat ? 'night' : 'common';
            addMessage(tab, { text: data.text, username: data.from, timestamp: new Date() });
          }
        }
      } catch (e) {
        console.error(e);
      }
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, [username, gameId, setGameState, setCurrentRole, addSheriffCheck, addDonCheck, setMafiaTeam, addMessage]);

  const sendMessage = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  return { connected, sendMessage };
}