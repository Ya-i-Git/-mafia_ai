import { useParams } from 'react-router-dom';
import { useWebSocket } from '../hooks/useWebSocket';
import { useGameStore } from '../stores/gameStore';
import { useChatStore } from '../stores/chatStore';
import { useAuthStore } from '../stores/authStore';
import ChatTabs from './ChatTabs';
import Timer from './Timer';
import { useState, useEffect, useMemo } from 'react';
import api from '../services/api';
import './GameBoard.css';

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

const getSheriffIcon = (roleCheck: string) => {
  if (roleCheck === 'мафия') return '🔪';
  return '👤';
};

export default function GameBoard() {
  const { gameId } = useParams<{ gameId: string }>();
  const gameState = useGameStore((state) => state.gameState);
  const currentRole = useGameStore((state) => state.currentRole);
  const sheriffChecks = useGameStore((state) => state.sheriffChecks);
  const donChecks = useGameStore((state) => state.donChecks);
  const mafiaTeam = useGameStore((state) => state.mafiaTeam);
  const mafiaDon = useGameStore((state) => state.mafiaDon);
  const doctorLastHealTarget = useGameStore((state) => state.doctorLastHealTarget);
  const resetChecks = useGameStore((state) => state.resetChecks);
  const { username } = useAuthStore();
  const { sendMessage } = useWebSocket(gameId!);
  const addMessage = useChatStore((state) => state.addMessage);
  const [nominatedTargetId, setNominatedTargetId] = useState<string | null>(null);
  const [actionPerformed, setActionPerformed] = useState(false);
  const [hasVoted, setHasVoted] = useState(false);

  const sortedPlayers = useMemo(() => {
    if (!gameState?.players) return [];
    return [...gameState.players].sort((a, b) => (a.number || 0) - (b.number || 0));
  }, [gameState?.players]);

  useEffect(() => {
    setActionPerformed(false);
  }, [gameState?.phase]);

  useEffect(() => {
    if (gameState?.phase === 'voting' || gameState?.phase === 'voting_tie') {
      setHasVoted(false);
    }
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

  const getCurrentActionText = () => {
    const phase = gameState?.phase;
    const speaker = gameState?.players?.find(p => p.id === gameState.current_speaker_id);
    switch (phase) {
      case 'day': return speaker ? `🎤 Речь: ${speaker.username}` : 'Дневное обсуждение';
      case 'nomination': return '⏳ Доп. время на номинирование';
      case 'defense':
      case 'defense_tie': return speaker ? `🛡️ Защищается: ${speaker.username}` : 'Защита';
      case 'voting':
      case 'voting_tie': return '🗳️ Голосование';
      case 'last_words': return speaker ? `💀 Последнее слово: ${speaker.username}` : 'Последнее слово';
      case 'night_mafia': return '🔪 Ход Мафии';
      case 'night_don': return '👑 Ход Дона';
      case 'night_sheriff': return '🕵️ Ход Шерифа';
      case 'night_doctor': return '💉 Ход Доктора';
      default: return '';
    }
  };

  const isNightPhase = gameState?.phase?.startsWith('night') ?? false;
  const bgClass = isNightPhase ? 'night-bg' : 'day-bg';

  if (!gameState) {
    return <div className="loading">Загрузка игры...</div>;
  }

  // Лобби
  if (gameState.phase === 'waiting') {
    const isOwner = gameState.owner_id === username;
    const minPlayers = 6;
    const currentPlayers = sortedPlayers.length;
    const canStart = isOwner && currentPlayers >= minPlayers;

    return (
      <div className="game-board waiting-lobby">
        <div className="lobby-container">
          <h2>Лобби игры #{gameId}</h2>
          <div className="players-list">
            <h3>Игроки ({currentPlayers} / {minPlayers}+)</h3>
            <div className="players-grid">
              {sortedPlayers.map((p, idx) => (
                <div key={p.id} className="player-card">
                  <div className="player-name">
                    {idx+1}. {p.username} {p.id === gameState.owner_id && '👑'}
                  </div>
                </div>
              ))}
            </div>
          </div>
          {isOwner && (
            <button className="start-game-btn" onClick={handleStartGame} disabled={!canStart}>
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

  // Предыгровая фаза
  if (gameState.phase === 'pre_game') {
    return (
      <div className="game-board pre-game">
        <div className="pre-game-container">
          <h2>Игра #{gameId}</h2>
          <div className="pre-game-timer">
            <Timer seconds={gameState.time_left ?? 0} onEnd={() => {}} />
          </div>
          <p>Игра начнётся через {gameState.time_left ?? 0} секунд...</p>
          {currentRole && (
            <div className="role-badge pre-game-role">
              {getRoleSticker(currentRole)} {currentRole}
            </div>
          )}
          <div className="players-list">
            <h3>Участники ({sortedPlayers.length})</h3>
            <div className="players-grid">
              {sortedPlayers.map((p) => (
                <div key={p.id} className="player-card">
                  <div className="player-name">
                    <span className="player-number">{p.number}.</span> {p.username}
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

  // Основная игра
  const currentPlayer = sortedPlayers.find(p => p.username === username);
  const isAlive = currentPlayer?.is_alive === true;
  const isActiveSpeaker = gameState.current_speaker_id === currentPlayer?.id;
  const isDefensePhase = gameState.phase === 'defense' || gameState.phase === 'defense_tie';
  const isCurrentDefender = isDefensePhase && gameState.current_speaker_id === currentPlayer?.id;
  const isLastWords = gameState.phase === 'last_words';
  const isCurrentLastWords = isLastWords && gameState.current_speaker_id === currentPlayer?.id;
  const currentActionText = getCurrentActionText();

  const handleSendChat = (text: string, chatType: string) => {
    sendMessage({ type: 'chat', text, chatType });
    addMessage(chatType as any, { text, username: 'Вы', timestamp: new Date() });
  };

  const handleEndTurn = () => {
    if (!isAlive && !isCurrentLastWords) return;
    sendMessage({ type: 'end_turn' });
  };

  const handleVote = (targetId: string) => {
    if (!isAlive) {
      addMessage('common', { text: 'Вы мертвы и не можете голосовать.', username: 'Система', timestamp: new Date() });
      return;
    }
    const target = sortedPlayers.find(p => p.id === targetId);
    if (target && target.id !== currentPlayer?.id) {
      sendMessage({ type: 'vote', target: target.username });
      setHasVoted(true);
    } else {
      addMessage('common', { text: 'Нельзя голосовать за себя.', username: 'Система', timestamp: new Date() });
    }
  };

  const handleNominate = (targetId: string) => {
    if (!isAlive) {
      addMessage('common', { text: 'Вы мертвы и не можете выдвигать.', username: 'Система', timestamp: new Date() });
      return;
    }
    const target = sortedPlayers.find(p => p.id === targetId);
    if (target && target.id !== currentPlayer?.id && target.is_alive) {
      sendMessage({ type: 'nominate', target: target.username });
      setNominatedTargetId(targetId);
      setTimeout(() => setNominatedTargetId(null), 2000);
    } else {
      addMessage('common', { text: 'Нельзя выдвигать мёртвого или себя.', username: 'Система', timestamp: new Date() });
    }
  };

  const isVotingPhase = gameState.phase === 'voting' || gameState.phase === 'voting_tie';
  const isNominationPhase = (gameState.phase === 'day' || gameState.phase === 'nomination') && (gameState.day_number || 0) > 1;
  const isNightPhaseForActions = gameState.phase.startsWith('night');
  const showNightActions = isNightPhaseForActions && isAlive && !actionPerformed && (
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
    if (!sortedPlayers) return [];
    if (currentRole === 'sheriff') {
      const checkedIds = Object.keys(sheriffChecks);
      return sortedPlayers.filter(p => p.is_alive && p.id !== currentPlayer?.id && !checkedIds.includes(p.id));
    }
    if (currentRole === 'don') {
      const checkedIds = Object.keys(donChecks);
      return sortedPlayers.filter(p => p.is_alive && p.id !== currentPlayer?.id && !checkedIds.includes(p.id));
    }
    return [];
  };

  const handleNightAction = (targetId: string) => {
    if (!nightActionType) return;
    const target = sortedPlayers.find(p => p.id === targetId);
    if (target && target.id !== currentPlayer?.id && target.is_alive) {
      sendMessage({ type: 'action', action: nightActionType, target: target.username });
      addMessage('common', { text: `Вы выбрали ${target.username} для ${actionLabel}`, username: 'Система', timestamp: new Date() });
      setActionPerformed(true);
    } else {
      addMessage('common', { text: 'Неверная цель', username: 'Система', timestamp: new Date() });
    }
  };

  return (
    <div className={`game-board ${bgClass}`}>
      <div className="game-header">
        <div className="player-role-display">
          {currentRole && <span className="role-badge">{getRoleSticker(currentRole)} {currentRole}</span>}
          {!isAlive && <span className="dead-badge">💀 Мёртв</span>}
          {isAlive && <span className="alive-badge">❤️ Жив</span>}
        </div>
        <div className="current-action">{currentActionText}</div>
        <div className="timer-display"><Timer seconds={gameState.time_left ?? 0} onEnd={() => {}} /></div>
      </div>

      {((isAlive && ((gameState.phase === 'day' || gameState.phase === 'nomination') && isActiveSpeaker)) || 
        isCurrentDefender || isCurrentLastWords) && (
        <button className="end-turn-btn" onClick={handleEndTurn}>
          ⏩ {isCurrentLastWords ? 'Завершить прощание' : (isCurrentDefender ? 'Пропустить речь' : 'Завершить речь')}
        </button>
      )}

      {/* Текстовые сообщения о союзниках УДАЛЕНЫ */}

      <div className="players-list">
        <h3>Игроки <span className="phase-indicator">{gameState.phase === 'day' ? '☀️ День' : '🌙 Ночь'}</span></h3>
        <div className="players-grid">
          {sortedPlayers.map((p) => {
            const isCurrent = p.id === currentPlayer?.id;
            const isDead = p.is_alive === false;
            const isNominatedByMe = nominatedTargetId === p.id;
            const canVoteForThis = isVotingPhase && isAlive && currentPlayer && gameState.voting_targets?.includes(p.id) && !hasVoted;
            const canNominateThis = isNominationPhase && isAlive && isActiveSpeaker && !isDead && !p.nominated;

            let mafiaAllyIcon = null;
            // Показываем значок союзника для мафии и дона
            if ((currentRole === 'mafia' || currentRole === 'don') && mafiaTeam && p.username !== username) {
              if (mafiaTeam.includes(p.username)) {
                const isDon = p.username === mafiaDon;
                mafiaAllyIcon = (
                  <span className="mafia-ally-badge" title={isDon ? "Дон" : "Союзник"}>
                    {isDon ? '👑' : '🔪'}
                  </span>
                );
              }
            }

            let sheriffCheckIcon = null;
            if (currentRole === 'sheriff' && sheriffChecks[p.id]) {
              sheriffCheckIcon = <span className="sheriff-check-badge">{getSheriffIcon(sheriffChecks[p.id])}</span>;
            }

            let donCheckIcon = null;
            if (currentRole === 'don' && donChecks[p.id] !== undefined) {
              donCheckIcon = <span className="don-check-badge">{donChecks[p.id] ? '🕵️' : '❌'}</span>;
            }

            return (
              <div key={p.id} className={`player-card ${isDead ? 'dead' : 'alive'} ${isCurrent ? 'current' : ''}`}>
                <div className="player-name">
                  <span className="player-number">{p.number}.</span> {p.username} {isCurrent && '(Вы)'}
                  {p.nominated && <span className="nominated-mark">📢</span>}
                  {mafiaAllyIcon}{sheriffCheckIcon}{donCheckIcon}
                </div>
                <div className="player-actions">
                  {canVoteForThis && <button onClick={() => handleVote(p.id)} className="vote-btn">🗳️ Голосовать</button>}
                  {canNominateThis && (
                    <button onClick={() => handleNominate(p.id)} className={`nominate-btn ${isNominatedByMe ? 'active' : ''}`}>
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
            {nightActionType === 'check' 
              ? getCheckablePlayers().map(p => <button key={p.id} onClick={() => handleNightAction(p.id)} className="night-action-btn">{p.username}</button>)
              : nightActionType === 'heal'
                ? sortedPlayers.filter(p => p.is_alive && p.id !== doctorLastHealTarget).map(p => <button key={p.id} onClick={() => handleNightAction(p.id)} className="night-action-btn">{p.username}</button>)
                : sortedPlayers.filter(p => p.is_alive && p.id !== currentPlayer?.id).map(p => <button key={p.id} onClick={() => handleNightAction(p.id)} className="night-action-btn">{p.username}</button>)}
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