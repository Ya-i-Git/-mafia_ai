import { useState } from 'react';
import { useAuthStore } from '../stores/authStore.ts';  // ← .ts
import api from '../services/api.ts';                    // ← .ts
import { useNavigate } from 'react-router-dom';

export default function Auth() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const { setToken } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async () => {
    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const res = await api.post(endpoint, { username, password });
      setToken(res.data.access_token);
      navigate('/lobby');
    } catch (err) {
      alert('Ошибка авторизации');
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
        />
        <input
          type="password"
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button onClick={handleSubmit}>{isLogin ? 'Войти' : 'Зарегистрироваться'}</button>
        <button className="switch-btn" onClick={() => setIsLogin(!isLogin)}>
          {isLogin ? 'Нет аккаунта? Зарегистрироваться' : 'Уже есть аккаунт? Войти'}
        </button>
      </div>
    </div>
  );
}