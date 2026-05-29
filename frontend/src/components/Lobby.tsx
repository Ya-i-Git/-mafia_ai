import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuthStore } from '../stores/authStore';

export default function Lobby() {
  const [gameCode, setGameCode] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { username, token } = useAuthStore();

  const createGame = async () => {
    if (!username) {
      alert('Ошибка: пользователь не авторизован');
      return;
    }
    setLoading(true);
    try {
      const res = await api.post('/lobby/create_game', { username });
      const gameId = res.data.game_id;
      console.log('Game created, game_id =', gameId);
      navigate(`/game/${gameId}`);
    } catch (err: any) {
      console.error('Create game error:', err);
      alert(err.response?.data?.detail || 'Не удалось создать игру');
    } finally {
      setLoading(false);
    }
  };

  const joinGame = async () => {
    const trimmedCode = gameCode.trim();
    if (!trimmedCode) {
      alert('Введите код игры');
      return;
    }
    if (!username) {
      alert('Ошибка: пользователь не авторизован');
      return;
    }
    setLoading(true);
    try {
      console.log(`Joining game ${trimmedCode} as ${username}`);
      const res = await api.post('/lobby/join_game', {
        game_id: trimmedCode,
        username: username,
      });
      console.log('Join response:', res.data);
      if (res.data.status === 'joined') {
        console.log('Redirecting to game page...');
        navigate(`/game/${trimmedCode}`);
      } else {
        alert('Не удалось присоединиться');
      }
    } catch (err: any) {
      console.error('Join error:', err);
      alert(err.response?.data?.detail || 'Не удалось присоединиться к игре');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="lobby">
      <div className="lobby-header">
        <h1>Лобби</h1>
        <div className="user-info">👤 {username}</div>
      </div>
      <div className="lobby-actions">
        <button className="create-btn" onClick={createGame} disabled={loading}>
          🎲 Создать игру
        </button>
        <div className="join-section">
          <input
            type="text"
            placeholder="Код игры"
            value={gameCode}
            onChange={(e) => setGameCode(e.target.value)}
            disabled={loading}
          />
          <button onClick={joinGame} disabled={loading}>
            🔑 Присоединиться
          </button>
        </div>
      </div>
      <button className="stats-link" onClick={() => navigate('/stats')}>
        📊 Статистика
      </button>
    </div>
  );
}