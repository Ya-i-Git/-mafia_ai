// frontend/src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Auth from './components/Auth';
import Lobby from './components/Lobby';
import GameBoard from './components/GameBoard';
import StatsDashboard from './components/StatsDashboard';
import ErrorBoundary from './components/ErrorBoundary';
import { useAuthStore } from './stores/authStore';

function App() {
  const token = useAuthStore((state) => state.token);

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/auth" element={<Auth />} />
          <Route
            path="/lobby"
            element={token ? <Lobby /> : <Navigate to="/auth" />}
          />
          <Route
            path="/game/:gameId"
            element={token ? <GameBoard /> : <Navigate to="/auth" />}
          />
          <Route
            path="/stats"
            element={token ? <StatsDashboard /> : <Navigate to="/auth" />}
          />
          <Route
            path="/"
            element={<Navigate to={token ? '/lobby' : '/auth'} />}
          />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;