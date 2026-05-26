import { useState } from 'react';
import { useChatStore } from '../stores/chatStore.ts';  // ← .ts
import './ChatTabs.css';

interface ChatTabsProps {
  gameId: string;
  isAlive: boolean;
  role: string | null;
  phase: 'day' | 'night' | 'voting';
  onSendMessage: (text: string, chatType: string) => void;
}

export default function ChatTabs({ isAlive, role, phase, onSendMessage }: ChatTabsProps) {
  const [activeTab, setActiveTab] = useState<'common' | 'dead' | 'night'>('common');
  const [message, setMessage] = useState('');
  const { messages, addMessage } = useChatStore();

  const showDeadTab = !isAlive;
  const showNightTab = role === 'mafia' && phase === 'night';

  const handleSend = () => {
    if (!message.trim()) return;
    onSendMessage(message, activeTab);
    addMessage(activeTab, { text: message, username: 'Вы', timestamp: new Date() });
    setMessage('');
  };

  const getTabIcon = (tab: string) => {
    switch(tab) {
      case 'common': return '💬';
      case 'dead': return '👻';
      case 'night': return '🌙';
      default: return '';
    }
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
              {getTabIcon(tab)} {tab === 'common' ? 'Общий' : tab === 'dead' ? 'Мёртвых' : 'Ночной'}
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