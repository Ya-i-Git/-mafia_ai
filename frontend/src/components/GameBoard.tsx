import { useParams } from 'react-router-dom';
import { useWebSocket } from '../hooks/useWebSocket';
import { useGameStore } from '../stores/gameStore';
import { useChatStore } from '../stores/chatStore';
import { useAuthStore } from '../stores/authStore';
import ChatTabs from './ChatTabs';
import Timer from './Timer';
import { useState, useEffect } from 'react';
import api from '../services/api';
import './GameBoard.css';

export default function GameBoard() {
  const { gameId } = useParams<{ gameId: string }>();
  const gameState = useGameStore((state) => state.gameState);
  const currentRole = useGameStore((state) => state.currentRole);
  const sheriffChecks = useGameStore((state) => state.sheriffChecks);
  const donChecks = useGameStore((state) => state.donChecks);
  const mafiaTeam = useGameStore((state) => state.mafiaTeam);
  const mafiaDon = useGameStore((state) => state.mafiaDon);
  const resetChecks = useGameStore((state) => state.resetChecks);
  const { username } = useAuthStore();
  const { sendMessage } = useWebSocket(gameId!);
  const addMessage = useChatStore((state) => state.addMessage);
  const [nominatedTargetId, setNominatedTargetId] = useState<string | null>(null);
  const [actionPerformed, setActionPerformed] = useState(false);

  useEffect(() => {
    setActionPerformed(false);
  }, [gameState?.phase]);

  useEffect(() => {
    if (currentRole) {
      resetChecks();
    }
  }, [currentRole, resetChecks]);

  const handleStartGame = async () => {
    if (!gameState || gameState.phase !== 'waiting') return;
    try {
      await api.post('/lobby/start_game', { game_id: gameId, username });
      addMessage('common', { text: 'Игра запущена!', username: 'Система', timestamp: new Date() });
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Не удалось начать игру');
    }
  };

  if (!gameState) {
    return <div className="loading">Загрузка игры...</div>;
  }

  // ЛОББИ
  if (gameState.phase === 'waiting') {
    const isOwner = gameState.owner_id === username;
    const minPlayers = 6;
    const currentPlayers = gameState.players?.length ?? 0;
    const canStart = isOwner && currentPlayers >= minPlayers;

    return (
      <div className="game-board waiting-lobby">
        <div className="lobby-container">
          <h2>Лобби игры #{gameId}</h2>
          <div className="players-list">
            <h3>Игроки ({currentPlayers} / {minPlayers}+)</h3>
            <div className="players-grid">
              {(gameState.players ?? []).map((p, idx) => (
                <div key={p.id} className="player-card">
                  <div className="player-name">
                    {idx+1}. {p.username} {p.id === gameState.owner_id && '👑'}
                  </div>
                </div>
              ))}
            </div>
          </div>
          {isOwner && (
            <button 
              className="start-game-btn" 
              onClick={handleStartGame} 
              disabled={!canStart}
            >
              {canStart ? 'Начать игру' : `Нужно ещё ${minPlayers - currentPlayers} игроков`}
            </button>
          )}
          <ChatTabs
            isAlive={false}
            role={null}
            phase={gameState.phase}
            onSendMessage={(text, chatType) => {
              sendMessage({ type: 'chat', text, chatType });
              addMessage('common', { text, username: 'Вы', timestamp: new Date() });
            }}
          />
        </div>
      </div>
    );
  }

  // ПРЕДЫГРОВАЯ ФАЗА
  if (gameState.phase === 'pre_game') {
    return (
      <div className="game-board pre-game">
        <div className="pre-game-container">
          <h2>Игра #{gameId}</h2>
          <div className="pre-game-timer">
            <Timer seconds={gameState.time_left ?? 0} onEnd={() => {}} />
          </div>
          <p>Игра начнётся через {gameState.time_left ?? 0} секунд...</p>
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
            onSendMessage={(text, chatType) => {
              sendMessage({ type: 'chat', text, chatType });
              addMessage('common', { text, username: 'Вы', timestamp: new Date() });
            }}
          />
        </div>
      </div>
    );
  }

  // ОСНОВНАЯ ИГРА
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

  const currentPlayer = gameState.players?.find(p => p.username === username);
  const isAlive = currentPlayer?.is_alive === true;
  const isActiveSpeaker = gameState.current_speaker_id === currentPlayer?.id;
  const isDefensePhase = gameState.phase === 'defense' || gameState.phase === 'defense_tie';
  const isCurrentDefender = isDefensePhase && gameState.current_speaker_id === currentPlayer?.id;

  const getActionTitle = () => {
    const phase = gameState.phase;
    const speaker = gameState.players?.find(p => p.id === gameState.current_speaker_id);
    switch (phase) {
      case 'day':
        return speaker ? `🎤 Сейчас речь: ${speaker.username}` : 'Дневное обсуждение';
      case 'nomination':
        return '⏳ Дополнительное время на номинирование';
      case 'defense':
      case 'defense_tie':
        return speaker ? `🛡️ Защищается: ${speaker.username}` : 'Защита';
      case 'voting':
      case 'voting_tie':
        return '🗳️ Голосование';
      case 'last_words':
        return speaker ? `💀 Последнее слово: ${speaker.username}` : 'Последнее слово';
      case 'night_mafia':
        return '🔪 Ход Мафии';
      case 'night_don':
        return '👑 Ход Дона';
      case 'night_sheriff':
        return '🕵️ Ход Шерифа';
      case 'night_doctor':
        return '💉 Ход Доктора';
      default:
        return '';
    }
  };

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
    if (phase.startsWith('night')) return '🌙 Ночь';
    return phase;
  };

  const isVotingPhase = gameState.phase === 'voting' || gameState.phase === 'voting_tie';
  const isNominationPhase = (gameState.phase === 'day' || gameState.phase === 'nomination') && (gameState.day_number || 0) > 1;

  const isNightPhase = gameState.phase.startsWith('night');
  const showNightActions = isNightPhase && isAlive && !actionPerformed && (
    (gameState.phase === 'night_mafia' && (currentRole === 'mafia' || currentRole === 'don')) ||
    (gameState.phase === 'night_don' && currentRole === 'don') ||
    (gameState.phase === 'night_sheriff' && currentRole === 'sheriff') ||
    (gameState.phase === 'night_doctor' && currentRole === 'doctor')
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

  const getCheckablePlayers = () => {
    if (!gameState.players) return [];
    if (currentRole === 'sheriff') {
      const checkedIds = Object.keys(sheriffChecks);
      return gameState.players.filter(p => p.is_alive && p.id !== currentPlayer?.id && !checkedIds.includes(p.id));
    }
    if (currentRole === 'don') {
      const checkedIds = Object.keys(donChecks);
      return gameState.players.filter(p => p.is_alive && p.id !== currentPlayer?.id && !checkedIds.includes(p.id));
    }
    return [];
  };

  const handleNightAction = (targetId: string) => {
    if (!nightActionType) return;
    const target = gameState.players?.find(p => p.id === targetId);
    if (target && target.id !== currentPlayer?.id && target.is_alive) {
      sendMessage({ type: 'action', action: nightActionType, target: target.username });
      addMessage('common', { text: `Вы выбрали ${target.username} для ${actionLabel}`, username: 'Система', timestamp: new Date() });
      setActionPerformed(true);
    } else {
      addMessage('common', { text: 'Неверная цель', username: 'Система', timestamp: new Date() });
    }
  };

  return (
    <div className="game-board">
      <div className="game-header">
        <h2>Игра #{gameId}</h2>
        <div className="game-status">
          <Timer seconds={gameState.time_left ?? 0} onEnd={() => {}} />
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
        {(isAlive && ((gameState.phase === 'day' || gameState.phase === 'nomination') && isActiveSpeaker) || isCurrentDefender) && (
          <button className="end-turn-btn" onClick={handleEndTurn}>
            ⏩ {isCurrentDefender ? 'Пропустить речь' : 'Завершить речь'}
          </button>
        )}
      </div>

      {/* Информация о мафии для мафии и дона */}
      {currentRole === 'mafia' && mafiaTeam && (
        <div className="mafia-info">
          🔪 Союзники: {mafiaTeam.join(', ')} {mafiaDon && `(Дон: ${mafiaDon})`}
        </div>
      )}
      {currentRole === 'don' && mafiaTeam && (
        <div className="mafia-info">
          👑 Вы — дон. Ваша команда: {mafiaTeam.filter(m => m !== username).join(', ')}
        </div>
      )}

      <div className="action-title">{getActionTitle()}</div>

      <div className="players-list">
        <h3>
          Игроки
          <span className="phase-indicator">{getPhaseIcon(gameState.phase)}</span>
        </h3>
        <div className="players-grid">
          {(gameState.players ?? []).map((p, idx) => {
            const isCurrent = p.id === currentPlayer?.id;
            const isDead = p.is_alive === false;
            const isNominatedByMe = nominatedTargetId === p.id;

            // Вычисляем возможность голосования и номинации для этого игрока
            const canVote = isVotingPhase && isAlive && currentPlayer && 
                            gameState.voting_targets?.includes(p.id) && p.id !== currentPlayer.id;
            const canNominate = isNominationPhase && isAlive && isActiveSpeaker && p.id !== currentPlayer?.id;

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
                {currentRole === 'sheriff' && sheriffChecks[p.id] && (
                  <div className="check-badge">🔍 {sheriffChecks[p.id]}</div>
                )}
                {currentRole === 'don' && donChecks[p.id] !== undefined && (
                  <div className="don-check">
                    {donChecks[p.id] ? '🕵️' : '❌'}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {showNightActions && (
        <div className="night-actions">
          <h4>{actionLabel}</h4>
          <div className="players-grid">
            {nightActionType === 'check' 
              ? getCheckablePlayers().map(p => (
                  <button key={p.id} onClick={() => handleNightAction(p.id)} className="night-action-btn">
                    {p.username}
                  </button>
                ))
              : gameState.players?.filter(p => p.is_alive && p.id !== currentPlayer?.id).map(p => (
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