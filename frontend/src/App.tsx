// frontend/src/App.tsx
import { useState, useEffect } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { UkraineMap } from './components/UkraineMap';

function App() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('access_token'));

  // Режим: 'login' або 'register'
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  const [usernameInput, setUsernameInput] = useState('');
  const [passwordInput, setPasswordInput] = useState('');
  const [authError, setAuthError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const roomId = "test_room";
  const { isConnected, gameState, sendMessage } = useWebSocket(roomId, token);

  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [numberAnswer, setNumberAnswer] = useState<string>('');
  const [hasAnswered, setHasAnswered] = useState<boolean>(false);

  const currentQuestionId = gameState?.current_question?.id;

  useEffect(() => {
    setHasAnswered(false);
    setSelectedOption(null);
    setNumberAnswer('');
  }, [currentQuestionId]);

  // Обробник кліку по області мапи (оголошуємо ТУТ, у тілі компонента!)
  const handleRegionClick = (regionId: string) => {
    if (gameState?.status === 'CLAIM_TERRITORY') {
      sendMessage('claim_region', { region_id: regionId });
    } else {
      console.log(`Зараз не фаза захоплення. Клікнули на: ${regionId}`);
    }
  };

  // Обробник Входу / Реєстрації
  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    setSuccessMessage(null);

    if (authMode === 'register') {
      // 1. РЕЄСТРАЦІЯ (JSON)
      try {
        const response = await fetch('http://127.0.0.1:8000/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: usernameInput,
            email: `${usernameInput.trim().toLowerCase()}@gmail.com`,
            password: passwordInput,
          }),
        });

        if (!response.ok) {
          const errData = await response.json();
          let errorMessage = 'Помилка реєстрації';
          if (typeof errData.detail === 'string') {
            errorMessage = errData.detail;
          } else if (Array.isArray(errData.detail)) {
            errorMessage = errData.detail.map((e: any) => e.msg).join(', ');
          }
          throw new Error(errorMessage);
        }

        setSuccessMessage('Акаунт успішно створено! Тепер увійдіть.');
        setAuthMode('login');
      } catch (err: any) {
        setAuthError(err.message || 'Помилка при реєстрації');
      }
    } else {
      // 2. ВХІД (JSON)
      try {
        const response = await fetch('http://127.0.0.1:8000/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: usernameInput,
            password: passwordInput,
          }),
        });

        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || 'Невірний логін або пароль');
        }

        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        setToken(data.access_token);
      } catch (err: any) {
        setAuthError(err.message || 'Помилка при вході');
      }
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
  };

  const handleSendAnswer = (answerValue: string) => {
    if (hasAnswered) return;
    sendMessage('submit_answer', { answer: answerValue });
    setHasAnswered(true);
  };

  // --- ЕКРАН АВТОРИЗАЦІЇ ---
  if (!token) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: '#0f172a',
        color: '#ffffff',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: 'sans-serif',
        padding: '20px'
      }}>
        <form onSubmit={handleAuth} style={{
          backgroundColor: '#1e293b',
          padding: '30px',
          borderRadius: '16px',
          maxWidth: '380px',
          width: '100%',
          boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.3)',
          border: '1px solid #334155',
          display: 'flex',
          flexDirection: 'column',
          gap: '15px'
        }}>
          <h2 style={{ textAlign: 'center', color: '#38bdf8', margin: '0 0 10px 0' }}>
            {authMode === 'login' ? 'Вхід у TriviaUA 🇺🇦' : 'Реєстрація у TriviaUA 🇺🇦'}
          </h2>

          {authError && (
            <div style={{
              backgroundColor: 'rgba(239, 68, 68, 0.2)',
              color: '#f87171',
              padding: '10px',
              borderRadius: '8px',
              fontSize: '14px',
              textAlign: 'center',
              border: '1px solid rgba(239, 68, 68, 0.4)'
            }}>
              {authError}
            </div>
          )}

          {successMessage && (
            <div style={{
              backgroundColor: 'rgba(34, 197, 94, 0.2)',
              color: '#4ade80',
              padding: '10px',
              borderRadius: '8px',
              fontSize: '14px',
              textAlign: 'center',
              border: '1px solid rgba(34, 197, 94, 0.4)'
            }}>
              {successMessage}
            </div>
          )}

          <div>
            <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '5px' }}>Юзернейм</label>
            <input
              type="text"
              required
              value={usernameInput}
              onChange={(e) => setUsernameInput(e.target.value)}
              placeholder="limoncell0"
              style={{
                width: '100%',
                padding: '10px',
                borderRadius: '8px',
                border: '1px solid #475569',
                backgroundColor: '#0f172a',
                color: '#fff',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '5px' }}>Пароль</label>
            <input
              type="password"
              required
              value={passwordInput}
              onChange={(e) => setPasswordInput(e.target.value)}
              placeholder="••••••••"
              style={{
                width: '100%',
                padding: '10px',
                borderRadius: '8px',
                border: '1px solid #475569',
                backgroundColor: '#0f172a',
                color: '#fff',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <button
            type="submit"
            style={{
              marginTop: '5px',
              padding: '12px',
              borderRadius: '8px',
              border: 'none',
              backgroundColor: '#2563eb',
              color: '#fff',
              fontWeight: 'bold',
              cursor: 'pointer'
            }}
          >
            {authMode === 'login' ? 'Увійти' : 'Зареєструватися'}
          </button>

          <p style={{ textAlign: 'center', fontSize: '13px', color: '#94a3b8', margin: '5px 0 0 0' }}>
            {authMode === 'login' ? 'Немає акаунту? ' : 'Вже є акаунт? '}
            <span
              onClick={() => {
                setAuthError(null);
                setSuccessMessage(null);
                setAuthMode(authMode === 'login' ? 'register' : 'login');
              }}
              style={{ color: '#38bdf8', cursor: 'pointer', fontWeight: 'bold', textDecoration: 'underline' }}
            >
              {authMode === 'login' ? 'Зареєструватися' : 'Увійти'}
            </span>
          </p>
        </form>
      </div>
    );
  }

  // --- ІГРОВИЙ ЕКРАН (Full Screen Layout ala Triviador) ---
  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0f172a',
      color: '#ffffff',
      fontFamily: 'sans-serif',
      display: 'flex',
      flexDirection: 'column',
      position: 'relative',
      overflow: 'hidden'
    }}>

      {/* 1. Мапа України - на весь екран по центру */}
      <div style={{
        position: 'absolute',
        top: '10%',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '100%',
        height: '80%',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 1, // Нижче ніж інтерфейс
        opacity: gameState ? 1 : 0.3
      }}>
        {gameState ? (
          <UkraineMap
            mapState={gameState.map_state || {}}
            players={gameState.players || []}
            onRegionClick={handleRegionClick}
          />
        ) : (
          <div style={{ color: '#94a3b8' }}>Підключення...</div>
        )}
      </div>

      {gameState && (
        <>
          {/* 2. Вертикальна панель гравців (зліва) */}
          <div style={{
            position: 'absolute',
            left: '20px',
            top: '20px',
            bottom: '20px',
            width: '280px',
            display: 'flex',
            flexDirection: 'column',
            gap: '15px',
            zIndex: 10 // Поверх мапи
          }}>

            {/* Статус кімнати та сокету */}
            <div style={{
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              backdropFilter: 'blur(10px)',
              padding: '15px',
              borderRadius: '16px',
              border: '1px solid #334155'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <h1 style={{ color: '#38bdf8', margin: 0, fontSize: '20px' }}>TriviaUA</h1>
                <span style={{
                  padding: '4px 10px',
                  borderRadius: '12px',
                  fontSize: '11px',
                  fontWeight: 'bold',
                  backgroundColor: isConnected ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  color: isConnected ? '#4ade80' : '#f87171',
                  border: isConnected ? '1px solid rgba(34, 197, 94, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)'
                }}>{isConnected ? 'ON' : 'OFF'}</span>
              </div>
              <span style={{ color: '#94a3b8', fontSize: '11px', display: 'block' }}>ФАЗА</span>
              <span style={{ fontSize: '15px', fontWeight: 'bold', color: '#facc15' }}>{gameState.status}</span>
            </div>

            {/* Таблиця гравців */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
              {gameState.players.map((player: any, index: number) => {
                const isMyTurn = gameState.current_turn_player_id === player.user_id;

                return (
                  <div key={player.user_id} style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    backgroundColor: isMyTurn ? 'rgba(59, 130, 246, 0.3)' : 'rgba(51, 65, 85, 0.8)',
                    backdropFilter: 'blur(5px)',
                    padding: '15px',
                    borderRadius: '12px',
                    border: `2px solid ${isMyTurn ? '#facc15' : player.color}`, // Золота рамка якщо хід цього гравця
                    boxShadow: isMyTurn ? '0 0 12px rgba(250, 204, 21, 0.4)' : 'none',
                    transition: 'all 0.3s'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ fontSize: '12px', color: '#94a3b8' }}>#{index + 1}</div>
                      <div>
                        <span style={{ fontWeight: '700', fontSize: '15px', display: 'block' }}>{player.username}</span>
                        {isMyTurn && <span style={{ fontSize: '10px', color: '#facc15', fontWeight: 'bold' }}>⚡ ХІД ГРАВЦЯ</span>}
                      </div>
                    </div>
                    <span style={{ fontWeight: 'bold', color: player.color, fontSize: '16px' }}>
                      {player.score} б.
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Кнопка виходу (в самому низу) */}
            <button
              onClick={handleLogout}
              style={{
                marginTop: 'auto',
                padding: '10px',
                borderRadius: '8px',
                border: '1px solid #475569',
                backgroundColor: 'transparent',
                color: '#94a3b8',
                fontSize: '12px',
                cursor: 'pointer'
              }}
            >Вийти 🚪</button>
          </div>

          {/* 3. Блок питання (по центру внизу) */}
          {gameState.current_question && (
            <div style={{
              position: 'absolute',
              bottom: '40px',
              left: '320px', // Щоб не наповзати на панель гравців
              right: '20px',
              maxWidth: '800px', // Обмежуємо ширину питання
              margin: '0 auto', // Центруємо в доступному просторі
              zIndex: 10,
              backgroundColor: 'rgba(30, 58, 138, 0.8)',
              backdropFilter: 'blur(10px)',
              padding: '25px',
              borderRadius: '16px',
              border: '1px solid rgba(59, 130, 246, 0.4)',
              display: 'flex',
              flexDirection: 'column',
              gap: '20px'
            }}>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <p style={{ fontSize: '20px', fontWeight: '600', margin: 0, lineHeight: '1.4', flex: 1, marginRight: '20px' }}>
                  {gameState.current_question.text}
                </p>

                {gameState.timer_seconds > 0 && (
                  <div style={{
                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                    padding: '8px 16px',
                    borderRadius: '12px',
                    border: '1px solid rgba(239, 68, 68, 0.4)',
                    minWidth: '70px',
                    textAlign: 'center'
                  }}>
                    <span style={{ fontSize: '24px', fontWeight: '900', color: '#f87171' }}>
                      {gameState.timer_seconds}s
                    </span>
                  </div>
                )}
              </div>

              {/* Варіанти відповіді */}
              {gameState.current_question.type === 'CHOICE' && gameState.current_question.options && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  {Object.entries(gameState.current_question.options).map(([key, value]) => (
                    <button
                      key={key}
                      disabled={hasAnswered}
                      onClick={() => {
                        setSelectedOption(key);
                        handleSendAnswer(key);
                      }}
                      className="option-btn"
                      style={{
                        padding: '15px',
                        borderRadius: '10px',
                        border: '1px solid #475569',
                        backgroundColor: selectedOption === key ? '#2563eb' : '#334155',
                        color: '#ffffff',
                        fontWeight: 'bold',
                        fontSize: '15px',
                        cursor: hasAnswered ? 'not-allowed' : 'pointer',
                        transition: 'all 0.2s',
                      }}
                    >
                      {key}: {value as string}
                    </button>
                  ))}
                </div>
              )}

              {gameState.current_question.type === 'NUMBER' && (
                <div style={{ display: 'flex', gap: '10px' }}>
                  <input
                    type="number"
                    placeholder="Введіть число..."
                    disabled={hasAnswered}
                    value={numberAnswer}
                    onChange={(e) => setNumberAnswer(e.target.value)}
                    style={{
                      flex: 1,
                      padding: '15px',
                      borderRadius: '10px',
                      border: '1px solid #475569',
                      backgroundColor: '#0f172a',
                      color: '#ffffff',
                      fontSize: '16px'
                    }}
                  />
                  <button
                    disabled={hasAnswered || !numberAnswer}
                    onClick={() => handleSendAnswer(numberAnswer)}
                    style={{
                      padding: '12px 25px',
                      borderRadius: '10px',
                      border: 'none',
                      backgroundColor: '#16a34a',
                      color: '#ffffff',
                      fontWeight: 'bold',
                      fontSize: '15px',
                      cursor: (hasAnswered || !numberAnswer) ? 'not-allowed' : 'pointer',
                    }}
                  >Надіслати</button>
                </div>
              )}

              {hasAnswered && (
                <p style={{ textAlign: 'center', color: '#4ade80', margin: '5px 0 0 0', fontSize: '14px', fontWeight: 'bold' }}>
                  ✓ Відповідь прийнято! Чекаємо...
                </p>
              )}
            </div>
          )}
        </>
      )}

    </div>
  );
}

export default App;