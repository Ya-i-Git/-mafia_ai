import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuthStore } from '../stores/authStore';
import { useGameStore } from '../stores/gameStore';

const MIN_PLAYERS = 6;

export default function Lobby() {
  const navigate = useNavigate();
  const { username } = useAuthStore();
  const { gameState, setGameState } = useGameStore();

  const [mode, setMode] = useState<'entry' | 'waiting'>('entry');
  const [gameId, setGameId] = useState<string | null>(null);
  const [joinCode, setJoinCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [ws, setWs] = useState<WebSocket | null>(null);

  const isCreator = gameState?.players.length ? gameState.players[0].username === username : false;
  const canStart = isCreator && (gameState?.players.length ?? 0) >= MIN_PLAYERS;

  // Подключение WebSocket при входе в комнату ожидания
  useEffect(() => {
    if (mode !== 'waiting' || !gameId) return;

    const wsUrl = `/ws/${gameId}?username=${encodeURIComponent(username)}`;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const fullUrl = `${protocol}//${window.location.host}${wsUrl}`;
    const socket = new WebSocket(fullUrl);
    setWs(socket);

    socket.onopen = () => console.log('[Lobby] WebSocket connected');
    
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'game_state') {
          console.log('[Lobby] Game state update:', data.state.phase);
          setGameState(data.state);
          
          // 👇 КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: если игра вышла из фазы ожидания – редирект
          if (data.state.phase !== 'waiting') {
            console.log('[Lobby] Game started, redirecting to /game/' + gameId);
            navigate(`/game/${gameId}`);
          }
        }
      } catch (err) {
        console.error('[Lobby] WS parse error:', err);
      }
    };
    
    socket.onerror = (err) => console.error('[Lobby] WS error:', err);
    socket.onclose = () => console.log('[Lobby] WebSocket disconnected');

    return () => {
      if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
        socket.close();
      }
    };
  }, [mode, gameId, username, setGameState, navigate]);

  // Создание игры
  const createGame = async () => {
    setLoading(true);
    setError('');
    try {
      const createRes = await api.post('/lobby/create_game');
      const newGameId = createRes.data.game_id;

      await api.post('/lobby/join_game', { game_id: newGameId, username });

      setGameId(newGameId);
      setMode('waiting');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Не удалось создать игру');
    } finally {
      setLoading(false);
    }
  };

  // Присоединение к игре
  const joinGame = async () => {
    if (!joinCode.trim()) {
      setError('Введите код игры');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await api.post('/lobby/join_game', { game_id: joinCode.trim(), username });
      setGameId(joinCode.trim());
      setMode('waiting');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Игра не найдена или уже началась');
    } finally {
      setLoading(false);
    }
  };

  // Старт игры (только для создателя)
  const startGame = async () => {
    if (!gameId) return;
    setLoading(true);
    try {
      await api.post('/lobby/start_game', { game_id: gameId, username });
      // После успешного старта сервер поменяет фазу, и все получат game_state с phase !== 'waiting'
      // Редирект произойдёт автоматически через WebSocket (см. socket.onmessage)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Не удалось начать игру');
    } finally {
      setLoading(false);
    }
  };

  // Выход из комнаты
  const leaveWaiting = () => {
    if (ws) ws.close();
    setMode('entry');
    setGameId(null);
    setGameState(null);
  };

  // ----- Отрисовка -----
  if (mode === 'waiting' && gameId) {
    const playerCount = gameState?.players.length ?? 0;
    const players = gameState?.players ?? [];

    return (
      <div className="lobby waiting-room">
        <div className="waiting-header">
          <h1>🎮 Комната ожидания</h1>
          <button className="leave-btn" onClick={leaveWaiting} disabled={loading}>
            ✕ Покинуть
          </button>
        </div>
        <div className="game-info">
          <p><strong>Код игры:</strong> {gameId}</p>
          <p><strong>Игроков:</strong> {playerCount} / {MIN_PLAYERS}+</p>
          {!gameState && <p className="info">Подключение к комнате...</p>}
        </div>

        <div className="players-list">
          <h3>👥 Участники</h3>
          <ul>
            {players.map((p, idx) => (
              <li key={p.id}>
                {p.username}
                {idx === 0 && <span className="creator-badge"> (создатель)</span>}
                {!p.is_alive && <span className="dead-badge"> 💀</span>}
              </li>
            ))}
          </ul>
        </div>

        {canStart && (
          <button className="start-btn" onClick={startGame} disabled={loading}>
            {loading ? 'Запуск...' : '🚀 Начать игру'}
          </button>
        )}

        {!canStart && isCreator && playerCount < MIN_PLAYERS && (
          <p className="hint">Ожидаем ещё {MIN_PLAYERS - playerCount} игроков...</p>
        )}

        {error && <div className="error-message">{error}</div>}
      </div>
    );
  }

  // Режим входа
  return (
    <div className="lobby entry-mode">
      <div className="lobby-header">
        <h1>🐺 Мафия Онлайн</h1>
        <div className="user-info">👤 {username}</div>
      </div>

      <div className="lobby-actions">
        <button className="create-btn" onClick={createGame} disabled={loading}>
          {loading ? 'Создание...' : '🎲 Создать игру'}
        </button>

        <div className="join-section">
          <input
            type="text"
            placeholder="Код игры"
            value={joinCode}
            onChange={(e) => setJoinCode(e.target.value)}
            disabled={loading}
          />
          <button onClick={joinGame} disabled={loading}>
            {loading ? 'Подключение...' : '🔑 Присоединиться'}
          </button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      <button className="stats-link" onClick={() => navigate('/stats')}>
        📊 Статистика
      </button>
    </div>
  );
}