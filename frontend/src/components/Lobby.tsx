import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api.ts';           // ← .ts
import { useAuthStore } from '../stores/authStore.ts'; // ← .ts

export default function Lobby() {
  const [gameCode, setGameCode] = useState('');
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const createGame = async () => {
    const res = await api.post('/games/create');
    navigate(`/game/${res.data.game_id}`);
  };

  const joinGame = async () => {
    const res = await api.post('/games/join', { code: gameCode });
    navigate(`/game/${res.data.game_id}`);
  };

  return (
    <div className="lobby">
      <div className="lobby-header">
        <h1>Лобби</h1>
        <div className="user-info">👤 {user?.username}</div>
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