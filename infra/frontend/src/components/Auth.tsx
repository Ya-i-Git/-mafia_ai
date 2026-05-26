// Auth.tsx
import { useState } from 'react';
import { useAuthStore } from '../stores/authStore.ts';
import api from '../services/api.ts';
import { useNavigate } from 'react-router-dom';

export default function Auth() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const { setToken } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async () => {
    // Валидация
    if (!username.trim()) {
      alert('Введите имя пользователя');
      return;
    }
    if (!password.trim()) {
      alert('Введите пароль');
      return;
    }

    setLoading(true);
    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      
      // Отправляем username и password (как требует бэкенд)
      const res = await api.post(endpoint, { 
        username: username.trim(), 
        password: password.trim() 
      });
      
      // Бэкенд возвращает { token: "username" }
      const token = res.data.token;
      setToken(token);
      
      // Опционально: сохраняем username в localStorage или store
      localStorage.setItem('username', username);
      
      navigate('/lobby');
    } catch (err: any) {
      console.error('Ошибка:', err);
      
      // Обработка разных ошибок от бэкенда
      if (err.response?.status === 401) {
        alert('Пользователь не найден. Зарегистрируйтесь сначала.');
      } else if (err.response?.status === 400) {
        alert('Пользователь уже существует. Войдите в аккаунт.');
      } else {
        alert('Ошибка авторизации. Проверьте подключение к серверу.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>🐺 Мафия Онлайн</h1>
        <input
          type="text"
          placeholder="Имя пользователя"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          disabled={loading}
        />
        <input
          type="password"
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={loading}
          onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
        />
        <button onClick={handleSubmit} disabled={loading}>
          {loading ? 'Загрузка...' : (isLogin ? 'Войти' : 'Зарегистрироваться')}
        </button>
        <button 
          className="switch-btn" 
          onClick={() => setIsLogin(!isLogin)}
          disabled={loading}
        >
          {isLogin ? 'Нет аккаунта? Зарегистрироваться' : 'Уже есть аккаунт? Войти'}
        </button>
      </div>
    </div>
  );
}