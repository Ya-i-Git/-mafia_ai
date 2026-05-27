import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuthStore } from '../stores/authStore';

export default function Lobby() {
  const [gameCode, setGameCode] = useState('');
  const navigate = useNavigate();
  const { username } = useAuthStore();

  const createGame = async () => {
    if (!username) {
      alert('Ошибка: пользователь не авторизован');
      return;
    }
    const res = await api.post('/lobby/create_game', { username });
    navigate(`/game/${res.data.game_id}`);
  };

  const joinGame = async () => {
    if (!gameCode.trim()) return;
    if (!username) {
      alert('Ошибка: пользователь не авторизован');
      return;
    }
    const res = await api.post('/lobby/join_game', {
      game_id: gameCode.trim(),
      username: username,
    });
    navigate(`/game/${res.data.game_id || gameCode.trim()}`);
  };

  return (
    <div className="lobby">
      <div className="lobby-header">
        <h1>Лобби</h1>
        <div className="user-info">👤 {username}</div>
      </div>
      <div className="lobby-actions">
        <button className="create-btn" onClick={createGame}>🎲 Создать игру</button>
        <div className="join-section">
          <input
            type="text"
            placeholder="Код игры"
            value={gameCode}
            onChange={(e) => setGameCode(e.target.value)}
          />
          <button onClick={joinGame}>🔑 Присоединиться</button>
        </div>
      </div>
      <button className="stats-link" onClick={() => navigate('/stats')}>📊 Статистика</button>
    </div>
  );
}