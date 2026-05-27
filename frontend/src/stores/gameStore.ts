import { create } from 'zustand';

export interface GameState {
  phase: string;
  day_number: number;
  players: Array<{
    id: string;
    username: string;
    is_alive: boolean;
    nominated: boolean;
  }>;
  time_left: number;
  nominated_players: string[];
  voting_targets: string[];
}

interface GameStore {
  gameState: GameState | null;
  currentRole: string | null;
  setGameState: (state: GameState) => void;
  setCurrentRole: (role: string) => void;
}

export const useGameStore = create<GameStore>((set) => ({
  gameState: null,
  currentRole: null,
  setGameState: (state) => set({ gameState: state }),
  setCurrentRole: (role) => set({ currentRole: role }),
}));