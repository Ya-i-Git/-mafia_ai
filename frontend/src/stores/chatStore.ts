import { create } from 'zustand';

interface ChatMessage {
  text: string;
  username: string;
  timestamp: Date;
}

interface ChatState {
  messages: {
    common: ChatMessage[];
    dead: ChatMessage[];
    night: ChatMessage[];
  };
  addMessage: (tab: 'common' | 'dead' | 'night', message: ChatMessage) => void;
  clearMessages: (tab?: 'common' | 'dead' | 'night') => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: {
    common: [],
    dead: [],
    night: [],
  },
  addMessage: (tab, message) =>
    set((state) => ({
      messages: {
        ...state.messages,
        [tab]: [...state.messages[tab], message],
      },
    })),
  clearMessages: (tab) =>
    set((state) => {
      if (tab) {
        return {
          messages: {
            ...state.messages,
            [tab]: [],
          },
        };
      }
      return {
        messages: {
          common: [],
          dead: [],
          night: [],
        },
      };
    }),
}));