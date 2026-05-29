import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: number;
  username: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  username: string | null;
  setToken: (token: string) => void;
  setUser: (user: User) => void;
  setUsername: (username: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      username: null,
      setToken: (token) => set({ token }),
      setUser: (user) => set({ user }),
      setUsername: (username) => set({ username }),
      logout: () => set({ token: null, user: null, username: null }),
    }),
    {
      name: 'auth-storage', // ключ в localStorage
    }
  )
);