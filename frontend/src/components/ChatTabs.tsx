import { useState, useRef, useEffect } from 'react';
import { useChatStore } from '../stores/chatStore';
import './ChatTabs.css';

interface ChatTabsProps {
  isAlive: boolean;
  role: string | null;
  phase: string;
  onSendMessage: (text: string, chatType: string) => void;
}

export default function ChatTabs({ isAlive, role, phase, onSendMessage }: ChatTabsProps) {
  const [activeTab, setActiveTab] = useState<'common' | 'dead' | 'night'>('common');
  const [message, setMessage] = useState('');
  const messages = useChatStore((state) => state.messages);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const autoScrollRef = useRef(true);
  const chatMessagesRef = useRef<HTMLDivElement>(null);

  const isLobby = phase === 'waiting' || phase === 'pre_game';
  const showDeadTab = !isAlive && !isLobby;
  const showNightTab = (role === 'mafia' || role === 'don') && phase === 'night_mafia';

  // Для мёртвых игроков: объединяем common + night (если мафия)
  const getMergedMessages = () => {
    if (!isAlive) {
      let merged = [...messages.common];
      if (role === 'mafia' || role === 'don') {
        merged = [...merged, ...messages.night];
      }
      // Сортируем по времени (старые сверху)
      return merged.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    }
    return messages[activeTab];
  };

  useEffect(() => {
    if (autoScrollRef.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [isAlive ? messages[activeTab] : getMergedMessages()]);

  const handleScroll = () => {
    const container = chatMessagesRef.current;
    if (container) {
      const isAtBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 50;
      autoScrollRef.current = isAtBottom;
    }
  };

  const handleSend = () => {
    if (!message.trim()) return;
    const targetTab = isLobby ? 'common' : activeTab;
    onSendMessage(message, targetTab);
    setMessage('');
    autoScrollRef.current = true;
  };

  // Для мёртвых игроков не показываем вкладки
  if (!isAlive && !isLobby) {
    const merged = getMergedMessages();
    return (
      <div className="chat-container">
        <div className="chat-messages" ref={chatMessagesRef} onScroll={handleScroll}>
          {merged.map((msg, idx) => (
            <div key={idx} className={`chat-message ${msg.username === 'Вы' ? 'own' : ''}`}>
              <strong>{msg.username}:</strong> {msg.text}
              <small>{new Date(msg.timestamp).toLocaleTimeString()}</small>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        <div className="chat-input">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Введите сообщение..."
          />
          <button onClick={handleSend}>Отправить</button>
        </div>
      </div>
    );
  }

  // Живые игроки (или лобби) – обычные вкладки
  return (
    <div className="chat-container">
      {!isLobby && (
        <div className="chat-tabs">
          <button className={activeTab === 'common' ? 'active' : ''} onClick={() => setActiveTab('common')}>
            💬 Общий
          </button>
          {showDeadTab && (
            <button className={activeTab === 'dead' ? 'active' : ''} onClick={() => setActiveTab('dead')}>
              👻 Мёртвых
            </button>
          )}
          {showNightTab && (
            <button className={activeTab === 'night' ? 'active' : ''} onClick={() => setActiveTab('night')}>
              🔪 Мафия
            </button>
          )}
        </div>
      )}

      <div className="chat-messages" ref={chatMessagesRef} onScroll={handleScroll}>
        {(isLobby ? messages.common : messages[activeTab])?.map((msg, idx) => (
          <div key={idx} className={`chat-message ${msg.username === 'Вы' ? 'own' : ''}`}>
            <strong>{msg.username}:</strong> {msg.text}
            <small>{new Date(msg.timestamp).toLocaleTimeString()}</small>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Введите сообщение..."
        />
        <button onClick={handleSend}>Отправить</button>
      </div>
    </div>
  );
}