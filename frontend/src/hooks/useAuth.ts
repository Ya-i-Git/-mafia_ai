import { useEffect } from 'react';
import { useAuthStore } from '../stores/authStore';
import api from '../services/api';

export function useAuth() {
  const { token, setUser, logout } = useAuthStore();  // ← убрал setToken

  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      api.get('/auth/me')
        .then(res => setUser(res.data))
        .catch(() => logout());
    }
  }, [token, setUser, logout]);

  return { isAuthenticated: !!token, logout };
}