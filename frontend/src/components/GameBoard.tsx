
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useWebSocket } from '../hooks/useWebSocket.ts';  // ← .ts
import { useAuthStore } from '../stores/authStore.ts';    // ← .ts
import ChatTabs from './ChatTabs.tsx';                    // ← .tsx
import Timer from './Timer.tsx';                          // ← .tsx
import './GameBoard.css';

interface GameState {
  phase: 'day' | 'night' | 'voting';
  timeLeft: number;
  isAlive: boolean;
  role: string | null;
  players: Array<{ id: number; username: string; isAlive: boolean }>;
}

export default function GameBoard() {
  const { gameId } = useParams();
  const { token } = useAuthStore();
  const [gameState, setGameState] = useState<GameState | null>(null);
  const { sendMessage, lastMessage, } = useWebSocket(token, gameId!);

  useEffect(() => {
    if (lastMessage) {
      const data = JSON.parse(lastMessage);
      if (data.type === 'game_state') {
        setGameState(data.state);
      }
    }
  }, [lastMessage]);

  const handleVote = (targetId: number) => {
    sendMessage(JSON.stringify({ type: 'vote', target_id: targetId }));
  };

  if (!gameState) return <div className="loading">Загрузка игры...</div>;

  return (
    <div className="game-board">
      <div className="game-header">
        <h2>Игра #{gameId}</h2>
        <div className="game-status">
          <Timer seconds={gameState.timeLeft} onEnd={() => console.log('phase ended')} />
          <div className="player-status">
            {gameState.isAlive ? '❤️ Жив' : '💀 Мёртв'}
            {gameState.role && <span className="role"> | {gameState.role}</span>}
          </div>
        </div>
      </div>

      <div className="players-list">
        <h3>Игроки ({gameState.players.length})</h3>
        <div className="players-grid">
          {gameState.players.map(p => (
            <div key={p.id} className={`player-card ${!p.isAlive ? 'dead' : ''}`}>
              <span>{p.username}</span>
              {gameState.phase === 'voting' && gameState.isAlive && p.isAlive && (
                <button onClick={() => handleVote(p.id)}>Голосовать</button>
              )}
            </div>
          ))}
        </div>
      </div>

      <ChatTabs
        gameId={gameId!}
        isAlive={gameState.isAlive}
        role={gameState.role}
        phase={gameState.phase}
        onSendMessage={(text, chatType) => {
          sendMessage(JSON.stringify({ type: 'chat', chatType, text }));
        }}
      />
    </div>
  );
}