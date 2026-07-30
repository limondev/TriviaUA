import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketMessage {
  action: string;
  data: any;
}

export const useWebSocket = (roomId: string, token: string | null) => {
  const [isConnected, setIsConnected] = useState(false);
  const [gameState, setGameState] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!roomId || !token) return;

    const wsUrl = `ws://127.0.0.1:8000/ws/game/${roomId}?token=${token}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('✅ WebSocket: успішно підключено!');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        console.log('📩 WebSocket отримано:', message);

        switch (message.action) {
          case 'room_state':
          case 'game_started':
            // Завжди оновлюємо ПОВНИЙ стан гри!
            setGameState({ ...message.data });
            break;

          case 'timer_tick':
            // Зберігаємо ВСІ поля prevState, змінюючи лише секундний таймер
            setGameState((prevState: any) => {
              if (!prevState) return null;
              return {
                ...prevState,
                timer_seconds: message.data.timer_seconds,
              };
            });
            break;

          default:
            break;
        }
      } catch (error) {
        console.error('Помилка парсингу WebSocket повідомлення:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('⚠️ WebSocket помилка:', error);
    };

    ws.onclose = () => {
      console.log('❌ WebSocket: з’єднання закрите.');
      setIsConnected(false);
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, [roomId, token]);

  const sendMessage = useCallback((action: string, data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action, data }));
    } else {
      console.warn('Неможливо відправити повідомлення: WebSocket не підключено.');
    }
  }, []);

  return { isConnected, gameState, sendMessage };
};