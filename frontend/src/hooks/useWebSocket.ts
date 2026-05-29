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
  const setDoctorLastHealTarget = useGameStore((state) => state.setDoctorLastHealTarget);
  const addMessage = useChatStore((state) => state.addMessage);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const audioQueueRef = useRef<HTMLAudioElement[]>([]);
  const isPlayingRef = useRef(false);
  const connectionAttempted = useRef(false);

  const playNextAudio = () => {
    if (isPlayingRef.current || audioQueueRef.current.length === 0) return;
    const audio = audioQueueRef.current.shift();
    if (audio) {
      isPlayingRef.current = true;
      audio.play().catch(e => console.warn('Audio play failed', e));
      audio.onended = () => {
        isPlayingRef.current = false;
        playNextAudio();
      };
    }
  };

  const playAudioBase64 = (base64: string) => {
    const audio = new Audio(`data:audio/mpeg;base64,${base64}`);
    audioQueueRef.current.push(audio);
    playNextAudio();
  };

  useEffect(() => {
    if (!username || !gameId) return;
    if (connectionAttempted.current) {
      console.log('WebSocket connection already attempted, skipping duplicate');
      return;
    }
    connectionAttempted.current = true;

    const wsUrl = `/ws/${gameId}?username=${encodeURIComponent(username)}`;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const fullUrl = `${protocol}//${window.location.host}${wsUrl}`;
    console.log('Connecting WebSocket to', fullUrl);
    const ws = new WebSocket(fullUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log(`WebSocket connected to game ${gameId}`);
      setConnected(true);
    };
    ws.onclose = (event) => {
      console.log(`WebSocket closed: code=${event.code}, reason=${event.reason}`);
      setConnected(false);
      connectionAttempted.current = false;
      if (event.code !== 1000) {
        console.log('Unexpected disconnect, reloading page in 2 seconds...');
        setTimeout(() => window.location.reload(), 2000);
      }
    };
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WS message:', data.type);
        if (data.type === 'game_state') {
          setGameState(data.state);
        } else if (data.type === 'role_assigned') {
          setCurrentRole(data.role);
        } else if (data.type === 'mafia_team') {
          setMafiaTeam(data.members, data.don);
        } else if (data.type === 'doctor_last_heal') {
          setDoctorLastHealTarget(data.target_id);
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
        } else if (data.type === 'audio') {
          playAudioBase64(data.data);
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
      connectionAttempted.current = false;
    };
  }, [username, gameId, setGameState, setCurrentRole, addSheriffCheck, addDonCheck, setMafiaTeam, setDoctorLastHealTarget, addMessage]);

  const sendMessage = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  return { connected, sendMessage };
}