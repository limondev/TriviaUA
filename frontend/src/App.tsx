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
      // 2. ВХІД (ТЕПЕР ТАКОЖ ЧИСТИЙ JSON!)
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

          {/* Перемикач режимів */}
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

  // --- ІГРОВИЙ ЕКРАН ---
  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0f172a',
      color: '#ffffff',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: 'sans-serif',
      padding: '20px'
    }}>
      <div style={{
        backgroundColor: '#1e293b',
        padding: '30px',
        borderRadius: '16px',
        maxWidth: '500px',
        width: '100%',
        boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.3)',
        border: '1px solid #334155'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h1 style={{ color: '#38bdf8', margin: 0, fontSize: '24px' }}>TriviaUA 🇺🇦</h1>
          <button
            onClick={handleLogout}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: '1px solid #475569',
              backgroundColor: 'transparent',
              color: '#94a3b8',
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            Вийти 🚪
          </button>
        </div>

        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
          paddingBottom: '15px',
          borderBottom: '1px solid #334155'
        }}>
          <span style={{ color: '#94a3b8' }}>Сокет:</span>
          <span style={{
            padding: '4px 10px',
            borderRadius: '12px',
            fontSize: '12px',
            fontWeight: 'bold',
            backgroundColor: isConnected ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
            color: isConnected ? '#4ade80' : '#f87171',
            border: isConnected ? '1px solid rgba(34, 197, 94, 0.4)' : '1px solid rgba(239, 68, 68, 0.4)'
          }}>
            {isConnected ? 'ОНЛАЙН' : 'ОФЛАЙН'}
          </span>
        </div>

        {gameState ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ color: '#94a3b8', fontSize: '12px', display: 'block' }}>ФАЗА ГРИ</span>
                <span style={{ fontSize: '16px', fontWeight: 'bold', color: '#facc15' }}>
                  {gameState.status}
                </span>
              </div>

              {gameState.timer_seconds > 0 && (
                <div style={{
                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                  padding: '8px 16px',
                  borderRadius: '12px',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  textAlign: 'center'
                }}>
                  <span style={{ fontSize: '22px', fontWeight: '900', color: '#f87171' }}>
                    ⏱️ {gameState.timer_seconds}s
                  </span>
                </div>
              )}
            </div>

            {gameState.current_question && (
              <div style={{
                backgroundColor: 'rgba(30, 58, 138, 0.2)',
                padding: '20px',
                borderRadius: '12px',
                border: '1px solid rgba(59, 130, 246, 0.3)'
              }}>
                <p style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px', lineHeight: '1.4' }}>
                  {gameState.current_question.text}
                </p>

                {gameState.current_question.type === 'CHOICE' && gameState.current_question.options && (
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    {Object.entries(gameState.current_question.options).map(([key, value]) => (
                      <button
                        key={key}
                        disabled={hasAnswered}
                        onClick={() => {
                          setSelectedOption(key);
                          handleSendAnswer(key);
                        }}
                        style={{
                          padding: '12px',
                          borderRadius: '8px',
                          border: '1px solid #475569',
                          backgroundColor: selectedOption === key ? '#2563eb' : '#334155',
                          color: '#ffffff',
                          fontWeight: 'bold',
                          cursor: hasAnswered ? 'not-allowed' : 'pointer',
                          opacity: hasAnswered && selectedOption !== key ? 0.5 : 1,
                          transition: 'all 0.2s'
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
                        padding: '12px',
                        borderRadius: '8px',
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
                        padding: '12px 20px',
                        borderRadius: '8px',
                        border: 'none',
                        backgroundColor: '#16a34a',
                        color: '#ffffff',
                        fontWeight: 'bold',
                        cursor: (hasAnswered || !numberAnswer) ? 'not-allowed' : 'pointer',
                        opacity: hasAnswered ? 0.5 : 1
                      }}
                    >
                      Надіслати
                    </button>
                  </div>
                )}

                {hasAnswered && (
                  <p style={{ textAlign: 'center', color: '#4ade80', marginTop: '15px', fontSize: '14px' }}>
                    ✓ Відповідь прийнято! Чекаємо на інших...
                  </p>
                )}
              </div>
            )}
            {/* Інтерактивна мапа України */}
<div style={{
  backgroundColor: '#0f172a',
  padding: '15px',
  borderRadius: '12px',
  border: '1px solid #334155'
}}>
  <span style={{ color: '#94a3b8', fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>
    КАРТА ТЕРИТОРІЙ
  </span>
  <UkraineMap
    mapState={gameState.map_state || {}}
    players={gameState.players || []}
    onRegionClick={(regionId) => {
      console.log('Клікнули на область:', regionId);
    }}
  />
</div>
            <div>
              <span style={{ color: '#94a3b8', fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>
                ТАБЛИЦЯ ГРАВЦІВ
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {gameState.players.map((player: any) => (
                  <div key={player.user_id} style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    backgroundColor: 'rgba(51, 65, 85, 0.4)',
                    padding: '12px',
                    borderRadius: '8px',
                    border: '1px solid #334155'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{
                        width: '12px',
                        height: '12px',
                        borderRadius: '50%',
                        backgroundColor: player.color
                      }} />
                      <span style={{ fontWeight: '600' }}>{player.username}</span>
                    </div>
                    <span style={{ fontWeight: 'bold', color: '#38bdf8' }}>
                      {player.score} балів
                    </span>
                  </div>
                ))}
              </div>
            </div>

          </div>
        ) : (
          <div style={{ textAlign: 'center', color: '#64748b', padding: '30px 0' }}>
            Підключення до кімнати...
          </div>
        )}
      </div>
    </div>
  );
}

export default App;