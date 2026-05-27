import { useParams } from 'react-router-dom';
import { useWebSocket } from '../hooks/useWebSocket';
import { useGameStore } from '../stores/gameStore';
import { useChatStore } from '../stores/chatStore';
import { useAuthStore } from '../stores/authStore';
import ChatTabs from './ChatTabs';
import Timer from './Timer';
import './GameBoard.css';

export default function GameBoard() {
  const { gameId } = useParams<{ gameId: string }>();
  const gameState = useGameStore((state) => state.gameState);
  const currentRole = useGameStore((state) => state.currentRole);
  const { username } = useAuthStore();
  const { sendMessage } = useWebSocket(gameId!);
  const addMessage = useChatStore((state) => state.addMessage);

  // Определяем, жив ли текущий игрок
  const currentPlayer = gameState?.players.find(p => p.username === username);
  const isAlive = currentPlayer?.is_alive ?? true;

  const handleVote = (targetId: string) => {
    const target = gameState?.players.find(p => p.id === targetId);
    if (target) {
      sendMessage({ type: 'vote', target: target.username });
    }
  };

  const handleNominate = (targetId: string) => {
    const target = gameState?.players.find(p => p.id === targetId);
    if (target) {
      sendMessage({ type: 'nominate', target: target.username });
    }
  };

  const handleEndTurn = () => {
    sendMessage({ type: 'end_turn' });
  };

  const handleSendChat = (text: string, chatType: string) => {
    sendMessage({ type: 'chat', text, chatType });
    addMessage(chatType as any, {
      text,
      username: 'Вы',
      timestamp: new Date(),
    });
  };

  if (!gameState) return <div className="loading">Загрузка игры...</div>;

  return (
    <div className="game-board">
      <div className="game-header">
        <h2>Игра #{gameId}</h2>
        <div className="game-status">
          <Timer seconds={gameState.time_left} onEnd={() => {}} />
          <div className="player-status">
            {currentRole && <span>Роль: {currentRole}</span>}
            {!isAlive && <span className="dead-badge">💀 Мёртв</span>}
          </div>
        </div>
        <button onClick={handleEndTurn}>Закончить ход</button>
      </div>

      <div className="players-list">
        <h3>Игроки ({gameState.players.length})</h3>
        <div className="players-grid">
          {gameState.players.map(p => (
            <div key={p.id} className={`player-card ${!p.is_alive ? 'dead' : ''}`}>
              <span>{p.username} {p.id === currentPlayer?.id && ' (Вы)'}</span>
              {gameState.phase === 'voting' && p.is_alive && p.id !== currentPlayer?.id && (
                <button onClick={() => handleVote(p.id)}>Голосовать</button>
              )}
              {gameState.phase === 'day' && p.is_alive && p.id !== currentPlayer?.id && (
                <button onClick={() => handleNominate(p.id)}>Выставить</button>
              )}
            </div>
          ))}
        </div>
      </div>

      <ChatTabs
        isAlive={isAlive}
        role={currentRole}
        phase={gameState.phase}
        onSendMessage={handleSendChat}
      />
    </div>
  );
}