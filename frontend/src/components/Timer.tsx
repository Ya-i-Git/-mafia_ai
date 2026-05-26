import  { useEffect, useState } from 'react';
import './Timer.css';

interface TimerProps {
  seconds: number;
  onEnd: () => void;
}

export default function Timer({ seconds, onEnd }: TimerProps) {
  const [timeLeft, setTimeLeft] = useState(seconds);

  useEffect(() => {
    setTimeLeft(seconds);
  }, [seconds]);

  useEffect(() => {
    if (timeLeft <= 0) {
      onEnd();
      return;
    }
    const timer = setInterval(() => setTimeLeft(prev => prev - 1), 1000);
    return () => clearInterval(timer);
  }, [timeLeft, onEnd]);

  const formatTime = () => {
    const mins = Math.floor(timeLeft / 60);
    const secs = timeLeft % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className={`timer ${timeLeft <= 5 ? 'urgent' : ''}`}>
      ⏱️ {formatTime()}
    </div>
  );
}