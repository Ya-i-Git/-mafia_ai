import { useEffect, useState } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, PieChart, Pie, Cell } from 'recharts';
import api from '../services/api.ts';
import './StatsDashboard.css';

interface GlobalStats {
  winrateByRole: Record<string, number>;
  gamesPerDay: Array<{ date: string; count: number }>;
  averageGameDuration: number;
  topPlayers: Array<{ username: string; wins: number }>;
}

export default function StatsDashboard() {
  const [stats, setStats] = useState<GlobalStats | null>(null);
  const [selectedUser, setSelectedUser] = useState('');
  const [userStats, setUserStats] = useState<any>(null);

  useEffect(() => {
    api.get('/stats/global').then(res => setStats(res.data));
  }, []);

  if (!stats) return <div className="loading">Загрузка статистики...</div>;

  const COLORS = ['#00f3ff', '#ff00ff', '#ffaa00', '#00ff88'];
  const pieData = Object.entries(stats.winrateByRole).map(([name, value]) => ({ name, value }));

  const loadUserStats = async () => {
    try {
      const res = await api.get(`/stats/user/${selectedUser}`);
      setUserStats(res.data);
    } catch (err) {
      alert('Игрок не найден');
    }
  };

  return (
    <div className="stats-dashboard">
      <h1>📊 Статистика Мафии</h1>
      
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Winrate по ролям</h3>
          <PieChart width={400} height={300}>
            <Pie data={pieData} dataKey="value" cx="50%" cy="50%" outerRadius={100} label>
              {pieData.map((_, index) => (  // ← ИСПРАВЛЕНО: добавил entry, index
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </div>

        <div className="stat-card">
          <h3>Игр по дням</h3>
          <LineChart width={500} height={300} data={stats.gamesPerDay}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="date" stroke="#888" />
            <YAxis stroke="#888" />
            <Tooltip />
            <Line type="monotone" dataKey="count" stroke="#00f3ff" strokeWidth={2} />
          </LineChart>
        </div>

        <div className="stat-card">
          <h3>Топ игроков</h3>
          <BarChart width={500} height={300} data={stats.topPlayers}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="username" stroke="#888" />
            <YAxis stroke="#888" />
            <Tooltip />
            <Bar dataKey="wins" fill="#ff00ff" />
          </BarChart>
        </div>

        <div className="stat-card">
          <h3>Средняя длительность игры</h3>
          <div className="big-number">{Math.round(Number(stats.averageGameDuration) / 60)} минут</div>
        </div>
      </div>

      <div className="player-stats-section">
        <h2>Статистика игрока</h2>
        <div className="player-search">
          <input
            type="text"
            placeholder="ID или имя игрока"
            value={selectedUser}
            onChange={(e) => setSelectedUser(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && loadUserStats()}
          />
          <button onClick={loadUserStats}>Показать</button>
        </div>
        {userStats && (
          <div className="player-stats">
            <div className="stat-row">
              <span>Всего игр:</span>
              <strong>{userStats.totalGames}</strong>
            </div>
            <div className="stat-row">
              <span>Побед:</span>
              <strong>{userStats.wins}</strong>
            </div>
            <div className="stat-row">
              <span>Поражений:</span>
              <strong>{userStats.losses}</strong>
            </div>
            <div className="stat-row">
              <span>Точность первого угадывания:</span>
              <strong>{userStats.firstGuessAccuracy}%</strong>
            </div>
            <div className="stat-row">
              <span>Любимая роль:</span>
              <strong>{userStats.favoriteRole}</strong>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}