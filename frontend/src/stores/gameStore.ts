import { create } from 'zustand';

export interface GameState {
  phase: string;
  day_number: number;
  players: Array<{
    id: string;
    username: string;
    is_alive: boolean;
    nominated: boolean;
    number: number;
  }>;
  time_left: number;
  nominated_players: string[];
  voting_targets: string[];
  current_speaker_id: string | null;
  owner_id: string;
}

interface GameStore {
  gameState: GameState | null;
  currentRole: string | null;
  sheriffChecks: Record<string, string>;
  donChecks: Record<string, boolean>;
  mafiaTeam: string[] | null;
  mafiaDon: string | null;
  doctorLastHealTarget: string | null;
  setGameState: (state: GameState | null) => void;
  setCurrentRole: (role: string | null) => void;
  addSheriffCheck: (playerId: string, role: string) => void;
  addDonCheck: (playerId: string, isSheriff: boolean) => void;
  setMafiaTeam: (members: string[], don: string) => void;
  setDoctorLastHealTarget: (targetId: string | null) => void;
  resetChecks: () => void;
}

export const useGameStore = create<GameStore>((set) => ({
  gameState: null,
  currentRole: null,
  sheriffChecks: {},
  donChecks: {},
  mafiaTeam: null,
  mafiaDon: null,
  doctorLastHealTarget: null,
  setGameState: (state) => set({ gameState: state }),
  setCurrentRole: (role) => set({ currentRole: role }),
  addSheriffCheck: (playerId, role) => set((state) => ({
    sheriffChecks: { ...state.sheriffChecks, [playerId]: role }
  })),
  addDonCheck: (playerId, isSheriff) => set((state) => ({
    donChecks: { ...state.donChecks, [playerId]: isSheriff }
  })),
  setMafiaTeam: (members, don) => set({ mafiaTeam: members, mafiaDon: don }),
  setDoctorLastHealTarget: (targetId) => set({ doctorLastHealTarget: targetId }),
  resetChecks: () => set({ sheriffChecks: {}, donChecks: {}, doctorLastHealTarget: null }),
}));