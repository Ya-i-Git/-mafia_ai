import { useState } from 'react';
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

  const showDeadTab = !isAlive;
  const showNightTab = (role === 'mafia' || role === 'don') && phase === 'night_mafia';

  const handleSend = () => {
    if (!message.trim()) return;
    onSendMessage(message, activeTab);
    setMessage('');
  };

  return (
    <div className="chat-container">
      <div className="chat-tabs">
        {(['common', 'dead', 'night'] as const).map(tab => {
          if (tab === 'dead' && !showDeadTab) return null;
          if (tab === 'night' && !showNightTab) return null;
          return (
            <button
              key={tab}
              className={activeTab === tab ? 'active' : ''}
              onClick={() => setActiveTab(tab)}
            >
              {tab === 'common' ? '💬 Общий' : tab === 'dead' ? '👻 Мёртвых' : '🌙 Ночной'}
            </button>
          );
        })}
      </div>

      <div className="chat-messages">
        {messages[activeTab]?.map((msg, idx) => (
          <div key={idx} className={`chat-message ${msg.username === 'Вы' ? 'own' : ''}`}>
            <strong>{msg.username}:</strong> {msg.text}
            <small>{new Date(msg.timestamp).toLocaleTimeString()}</small>
          </div>
        ))}
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