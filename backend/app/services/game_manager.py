import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.all_models import Question
from app.services.websocket_maps import manager  # Наш WS-транспорт


class GameSession:
    def __init__(self, game_id: str):
        self.game_id: str = game_id
        self.status: str = "LOBBY"  # Можливі стани: LOBBY, PHASE_1_CAPTURE, PHASE_2_DUEL, FINISHED
        self.players: List[Dict[str, Any]] = []  # [{"user_id": "...", "username": "...", "score": 0, "color": "..."}]
        self.map_state: Dict[str, Any] = {}  # "UA-32" (Київська) -> {"owner_id": None, "score_value": 100}
        self.current_answers: Dict[str, Any] = {}
        # Логіка поточного ходу / квізу
        self.current_question: Optional[Dict[str, Any]] = None
        self.timer_task: Optional[asyncio.Task] = None
        self.timer_seconds: int = 0

    def to_dict(self) -> dict:
        """Перетворює стейт гри в чистий словник для відправки по WS"""
        return {
            "game_id": self.game_id,
            "status": self.status,
            "players": self.players,
            "map_state": self.map_state,
            "timer_seconds": self.timer_seconds,
            "current_question": self.current_question
        }


class GameManager:
    def __init__(self):
        # Хранилище активних сесій: { room_id: GameSession }
        self.active_games: Dict[str, GameSession] = {}

    def get_or_create_game(self, room_id: str) -> GameSession:
        if room_id not in self.active_games:
            self.active_games[room_id] = GameSession(room_id)
        return self.active_games[room_id]

    async def add_player_to_game(self, room_id: str, user_id: str, username: str):
        game = self.get_or_create_game(room_id)

        # Перевіряємо, чи гравець вже є в грі
        if any(p["user_id"] == user_id for p in game.players):
            return game

        # Призначаємо колір залежно від кількості гравців
        colors = ["red", "blue", "green"]
        player_color = colors[len(game.players) % 3]

        game.players.append({
            "user_id": user_id,
            "username": username,
            "score": 0,
            "color": player_color
        })

        # Якщо зібралося 3 гравці — автоматично запускаємо гру
        if len(game.players) == 3 and game.status == "LOBBY":
            await self.start_game(room_id)

        return game

    async def remove_player_from_game(self, room_id: str, user_id: str):
        if room_id in self.active_games:
            game = self.active_games[room_id]
            game.players = [p for p in game.players if p["user_id"] != user_id]

            # Якщо кімната порожня — видаляємо сесію з пам'яті
            if not game.players:
                if game.timer_task:
                    game.timer_task.cancel()
                del self.active_games[room_id]

    async def start_game(self, room_id: str):
        game = self.active_games[room_id]
        game.status = "PHASE_1_CAPTURE"

        # Ініціалізуємо карту України базовими секторами для MVP (наприклад, 3 області)
        # На фронтенді це будуть ID з SVG-мапи
        game.map_state = {
            "UA-32": {"owner_id": None, "name": "Київська область"},
            "UA-46": {"owner_id": None, "name": "Львівська область"},
            "UA-63": {"owner_id": None, "name": "Харківська область"},
        }

        # Сповіщаємо всіх, що гра стартувала
        await manager.broadcast_to_room(room_id, {
            "action": "game_started",
            "data": game.to_dict()
        })

        # Одразу запускаємо перше питання
        await self.next_question(room_id)

    async def next_question(self, room_id: str):
        game = self.active_games[room_id]
        game.current_answers = {}

        # Витягуємо випадкове питання з бази даних
        async with AsyncSessionLocal() as session:
            # Для MVP беремо просто одне випадкове питання
            # (У Postgres ORDER BY RANDOM() для великих баз повільний, але для MVP — ідеально)
            result = await session.execute(select(Question).order_by(Question.id))
            questions = result.scalars().all()

            if questions:
                # Беремо перше (можна зробити вибір за ігровою логікою)
                import random
                q = random.choice(questions)
                game.current_question = {
                    "id": q.id,
                    "type": q.type,
                    "text": q.text,
                    "options": q.options  # JSON з варіантами або None
                }
            else:
                game.current_question = {"text": "Питання в базі закінчилися!", "type": "CHOICE", "options": {}}

        # Запускаємо асинхронний таймер на 15 секунд для відповіді
        game.timer_seconds = 15
        if game.timer_task:
            game.timer_task.cancel()
        game.timer_task = asyncio.create_task(self._game_timer_loop(room_id))

    async def _game_timer_loop(self, room_id: str):
        game = self.active_games.get(room_id)
        if not game:
            return

        try:
            while game.timer_seconds > 0:
                await asyncio.sleep(1)
                game.timer_seconds -= 1
                # Кожну секунду транслюємо тікання таймеру на фронтенд
                await manager.broadcast_to_room(room_id, {
                    "action": "timer_tick",
                    "data": {"timer_seconds": game.timer_seconds}
                })

            # Коли час вийшов — фіксуємо кінець раунду
            await self.handle_round_timeout(room_id)

        except asyncio.CancelledError:
            # Таймер було скасовано штучно (наприклад, всі відповіли раніше часу)
            pass

    async def handle_round_timeout(self, room_id: str):
        game = self.active_games[room_id]
        correct = game.current_question.get("correct_answer") if game.current_question else None

        results = []
        for player in game.players:
            u_id = player["user_id"]
            user_ans = game.current_answers.get(u_id)

            is_correct = False
            points_gained = 0

            if user_ans and str(user_ans["answer"]).strip().upper() == str(correct).strip().upper():
                is_correct = True
                # Нараховуємо бали: 100 базових + бонус за швидкість (залишок секунд * 10)
                points_gained = 100 + (user_ans["time_left"] * 10)
                player["score"] += points_gained

            results.append({
                "username": player["username"],
                "is_correct": is_correct,
                "points_gained": points_gained,
                "total_score": player["score"]
            })

        # Транслюємо результати раунду всім гравцям
        await manager.broadcast_to_room(room_id, {
            "action": "round_results",
            "data": {
                "correct_answer": correct,
                "results": results,
                "players": game.players
            }
        })

        await asyncio.sleep(4)  # 4 секунди на показ результатів
        await self.next_question(room_id)

    async def submit_answer(self, room_id: str, user_id: str, answer: str):
        game = self.active_games.get(room_id)
        if not game or not game.current_question:
            return

        # Якщо гравець уже відповів у цьому раунді — ігноруємо
        if user_id in game.current_answers:
            return

        # Фіксуємо відповідь та скільки секунд залишалося на таймері
        game.current_answers[user_id] = {
            "answer": answer,
            "time_left": game.timer_seconds
        }

        # Якщо ВСІ гравці вже відповіли — можна зупинити таймер достроково
        if len(game.current_answers) == len(game.players):
            if game.timer_task:
                game.timer_task.cancel()
            await self.handle_round_timeout(room_id)


# Ініціалізуємо глобальний сервіс менеджменту ігор
game_manager = GameManager()