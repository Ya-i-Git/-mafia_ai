// frontend/src/components/ChatTabs.tsx
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

  // Автоскролл при новых сообщениях, если пользователь не скроллил вверх
  useEffect(() => {
    if (autoScrollRef.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages[activeTab]]);

  const handleScroll = () => {
    const container = chatMessagesRef.current;
    if (container) {
      const isAtBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 50;
      autoScrollRef.current = isAtBottom;
    }
  };

  const showDeadTab = !isAlive;
  const showNightTab = (role === 'mafia' || role === 'don') && phase === 'night_mafia';

  const handleSend = () => {
    if (!message.trim()) return;
    onSendMessage(message, activeTab);
    setMessage('');
    autoScrollRef.current = true; // после отправки включаем автоскролл
  };

  return (
    <div className="chat-container">
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

      <div className="chat-messages" ref={chatMessagesRef} onScroll={handleScroll}>
        {messages[activeTab]?.map((msg, idx) => (
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