// frontend/src/components/GameBoard.tsx
import { useParams } from 'react-router-dom';
import { useWebSocket } from '../hooks/useWebSocket';
import { useGameStore } from '../stores/gameStore';
import { useChatStore } from '../stores/chatStore';
import { useAuthStore } from '../stores/authStore';
import ChatTabs from './ChatTabs';
import Timer from './Timer';
import { useEffect, useState, useRef } from 'react';
import './GameBoard.css';

export default function GameBoard() {
  const { gameId } = useParams<{ gameId: string }>();
  const gameState = useGameStore((state) => state.gameState);
  const currentRole = useGameStore((state) => state.currentRole);
  const { username } = useAuthStore();
  const { sendMessage } = useWebSocket(gameId!);
  const addMessage = useChatStore((state) => state.addMessage);

  const [displayTime, setDisplayTime] = useState<number>(0);
  const [nominatedTargetId, setNominatedTargetId] = useState<string | null>(null);
  const timerIntervalRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastServerTimeRef = useRef<number | null>(null);

  // Стикеры для ролей
  const getRoleSticker = (role: string | null) => {
    if (!role) return '👤';
    switch (role) {
      case 'mafia': return '🔪';
      case 'don': return '👑';
      case 'sheriff': return '🕵️';
      case 'doctor': return '💉';
      default: return '👤';
    }
  };

  // Локальный таймер
  useEffect(() => {
    if (!gameState || gameState.time_left === undefined) return;
    const serverTime = gameState.time_left;
    if (lastServerTimeRef.current !== serverTime) {
      lastServerTimeRef.current = serverTime;
      setDisplayTime(serverTime);
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
      if (serverTime > 0) {
        timerIntervalRef.current = setInterval(() => {
          setDisplayTime((prev) => {
            const next = prev - 1;
            if (next <= 0) {
              if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
              timerIntervalRef.current = null;
              return 0;
            }
            return next;
          });
        }, 1000);
      }
    }
    return () => {
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    };
  }, [gameState?.time_left, gameState?.phase]);

  if (!gameState) {
    return <div className="loading">Загрузка игры...</div>;
  }

  const isPreGame = gameState.phase === 'pre_game';
  const currentPlayer = gameState.players?.find(p => p.username === username);
  const isAlive = currentPlayer?.is_alive === true;

  const handleSendChat = (text: string, chatType: string) => {
    sendMessage({ type: 'chat', text, chatType });
    addMessage(chatType as any, {
      text,
      username: 'Вы',
      timestamp: new Date(),
    });
  };

  const handleEndTurn = () => {
    if (!isAlive) return;
    sendMessage({ type: 'end_turn' });
  };

  const handleVote = (targetId: string) => {
    if (!isAlive) {
      addMessage('common', { text: 'Вы мертвы и не можете голосовать.', username: 'Система', timestamp: new Date() });
      return;
    }
    const target = gameState.players?.find(p => p.id === targetId);
    if (target && target.id !== currentPlayer?.id) {
      sendMessage({ type: 'vote', target: target.username });
    } else {
      addMessage('common', { text: 'Нельзя голосовать за себя.', username: 'Система', timestamp: new Date() });
    }
  };

  const handleNominate = (targetId: string) => {
    if (!isAlive) {
      addMessage('common', { text: 'Вы мертвы и не можете выдвигать.', username: 'Система', timestamp: new Date() });
      return;
    }
    const target = gameState.players?.find(p => p.id === targetId);
    if (target && target.id !== currentPlayer?.id) {
      sendMessage({ type: 'nominate', target: target.username });
      setNominatedTargetId(targetId);
      setTimeout(() => setNominatedTargetId(null), 2000);
    } else {
      addMessage('common', { text: 'Нельзя выдвигать себя.', username: 'Система', timestamp: new Date() });
    }
  };

  const getPhaseIcon = (phase: string) => {
    if (phase === 'day') return '☀️ День';
    if (phase === 'night' || phase.startsWith('night')) return '🌙 Ночь';
    return phase;
  };

  const isVotingPhase = gameState.phase === 'voting' || gameState.phase === 'voting_tie';
  const isNominationPhase = gameState.phase === 'day' && (gameState.day_number || 0) > 1;

  // Ночные действия
  const isNightPhase = gameState.phase.startsWith('night');
  const showNightActions = isNightPhase && isAlive && (
    (currentRole === 'mafia' || currentRole === 'don') ||
    currentRole === 'sheriff' ||
    currentRole === 'doctor'
  );

  let nightActionType: 'kill' | 'check' | 'heal' | null = null;
  let actionLabel = '';
  if (gameState.phase === 'night_mafia' && (currentRole === 'mafia' || currentRole === 'don')) {
    nightActionType = 'kill';
    actionLabel = '🔪 Убить';
  } else if (gameState.phase === 'night_don' && currentRole === 'don') {
    nightActionType = 'check';
    actionLabel = '🕵️ Проверить (шериф?)';
  } else if (gameState.phase === 'night_sheriff' && currentRole === 'sheriff') {
    nightActionType = 'check';
    actionLabel = '🔍 Проверить роль';
  } else if (gameState.phase === 'night_doctor' && currentRole === 'doctor') {
    nightActionType = 'heal';
    actionLabel = '💉 Вылечить';
  }

  const handleNightAction = (targetId: string) => {
    if (!nightActionType) return;
    const target = gameState.players?.find(p => p.id === targetId);
    if (target && target.id !== currentPlayer?.id && target.is_alive) {
      sendMessage({ type: 'action', action: nightActionType, target: target.username });
      addMessage('common', { text: `Вы выбрали ${target.username} для ${actionLabel}`, username: 'Система', timestamp: new Date() });
    } else {
      addMessage('common', { text: 'Неверная цель', username: 'Система', timestamp: new Date() });
    }
  };

  if (isPreGame) {
    return (
      <div className="game-board pre-game">
        <div className="pre-game-container">
          <h2>Игра #{gameId}</h2>
          <div className="pre-game-timer">
            <Timer seconds={displayTime} onEnd={() => {}} />
          </div>
          <p>Игра начнётся через {displayTime} секунд...</p>
          <div className="players-list">
            <h3>Участники ({gameState.players?.length ?? 0})</h3>
            <div className="players-grid">
              {(gameState.players ?? []).map((p, idx) => (
                <div key={p.id} className="player-card">
                  <div className="player-name">
                    <span className="player-number">{idx + 1}.</span> {p.username}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <ChatTabs
            isAlive={false}
            role={null}
            phase={gameState.phase}
            onSendMessage={handleSendChat}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="game-board">
      <div className="game-header">
        <h2>Игра #{gameId}</h2>
        <div className="game-status">
          <Timer seconds={displayTime} onEnd={() => {}} />
          <div className="player-status">
            {currentRole && (
              <span className="role-badge">
                {getRoleSticker(currentRole)} {currentRole}
              </span>
            )}
            {!isAlive && <span className="dead-badge">💀 Мёртв</span>}
            {isAlive && <span className="alive-badge">❤️ Жив</span>}
          </div>
        </div>
        {isAlive && (
          <button className="end-turn-btn" onClick={handleEndTurn}>
            {gameState.phase === 'day' ? '⏩ Завершить речь' : '✔️ Завершить ход'}
          </button>
        )}
      </div>

      <div className="players-list">
        <h3>
          Игроки
          <span className="phase-indicator">{getPhaseIcon(gameState.phase)}</span>
        </h3>
        <div className="players-grid">
          {(gameState.players ?? []).map((p, idx) => {
            const isCurrent = p.id === currentPlayer?.id;
            const isDead = p.is_alive === false;
            const canVote = isVotingPhase && !isDead && !isCurrent && isAlive;
            const canNominate = isNominationPhase && !isDead && !isCurrent && isAlive;
            const isNominatedByMe = nominatedTargetId === p.id;

            return (
              <div key={p.id} className={`player-card ${isDead ? 'dead' : 'alive'} ${isCurrent ? 'current' : ''}`}>
                <div className="player-name">
                  <span className="player-number">{idx + 1}.</span> {p.username} {isCurrent && '(Вы)'}
                  {p.nominated && <span className="nominated-mark">📢</span>}
                </div>
                <div className="player-actions">
                  {canVote && (
                    <button onClick={() => handleVote(p.id)} className="vote-btn">
                      🗳️ Голосовать
                    </button>
                  )}
                  {canNominate && (
                    <button
                      onClick={() => handleNominate(p.id)}
                      className={`nominate-btn ${isNominatedByMe ? 'active' : ''}`}
                    >
                      🎤 Выставить
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {showNightActions && (
        <div className="night-actions">
          <h4>{actionLabel}</h4>
          <div className="players-grid">
            {gameState.players?.filter(p => p.is_alive && p.id !== currentPlayer?.id).map(p => (
              <button key={p.id} onClick={() => handleNightAction(p.id)} className="night-action-btn">
                {p.username}
              </button>
            ))}
          </div>
        </div>
      )}

      <ChatTabs
        isAlive={isAlive}
        role={currentRole}
        phase={gameState.phase}
        onSendMessage={handleSendChat}
      />
    </div>
  );
}