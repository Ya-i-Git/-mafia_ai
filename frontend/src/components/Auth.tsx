import { useState } from 'react';
import { useAuthStore } from '../stores/authStore';
import api from '../services/api';
import { useNavigate } from 'react-router-dom';

export default function Auth() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const { setToken, setUsername: saveUsername } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async () => {
    if (!username.trim() || !password.trim()) { alert('Заполните поля'); return; }
    setLoading(true);
    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const res = await api.post(endpoint, { username: username.trim(), password: password.trim() });
      setToken(res.data.token);
      saveUsername(username.trim());
      navigate('/lobby');
    } catch (err: any) {
      if (err.response?.status === 401) alert('Пользователь не найден. Зарегистрируйтесь.');
      else if (err.response?.status === 400) alert('Пользователь уже существует. Войдите.');
      else alert('Ошибка авторизации.');
    } finally { setLoading(false); }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>🐺 Мафия Онлайн</h1>
        <input type="text" placeholder="Имя пользователя" value={username} onChange={(e) => setUsername(e.target.value)} disabled={loading} />
        <input type="password" placeholder="Пароль" value={password} onChange={(e) => setPassword(e.target.value)} disabled={loading} onKeyPress={(e) => e.key === 'Enter' && handleSubmit()} />
        <button onClick={handleSubmit} disabled={loading}>{loading ? 'Загрузка...' : isLogin ? 'Войти' : 'Зарегистрироваться'}</button>
        <button className="switch-btn" onClick={() => setIsLogin(!isLogin)} disabled={loading}>{isLogin ? 'Нет аккаунта? Зарегистрироваться' : 'Уже есть аккаунт? Войти'}</button>
      </div>
    </div>
  );
}