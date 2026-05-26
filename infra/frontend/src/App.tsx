import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Auth from './components/Auth.tsx';           // ← добавьте .tsx
import Lobby from './components/Lobby.tsx';         // ← добавьте .tsx
import GameBoard from './components/GameBoard.tsx'; // ← добавьте .tsx
import StatsDashboard from './components/StatsDashboard.tsx'; // ← добавьте .tsx
import { useAuthStore } from './stores/authStore.ts'; // ← добавьте .ts

function App() {
  const { token } = useAuthStore();
  
  return (
    <BrowserRouter>
      <div className="app">
        <Routes>
          <Route path="/auth" element={<Auth />} />
          <Route path="/lobby" element={token ? <Lobby /> : <Navigate to="/auth" />} />
          <Route path="/game/:gameId" element={token ? <GameBoard /> : <Navigate to="/auth" />} />
          <Route path="/stats" element={token ? <StatsDashboard /> : <Navigate to="/auth" />} />
          <Route path="/" element={<Navigate to={token ? "/lobby" : "/auth"} />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;