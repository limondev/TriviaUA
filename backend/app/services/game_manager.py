import asyncio
import random
from typing import Dict, List, Any, Optional
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.all_models import Question
from app.services.websocket_maps import manager  # Наш WS-транспорт


class GameSession:
    def __init__(self, game_id: str):
        self.game_id: str = game_id
        # Можливі стани: LOBBY, CLAIM_TERRITORY, QUESTION, FINISHED
        self.status: str = "LOBBY"
        self.players: List[Dict[str, Any]] = []  # [{"user_id": "...", "username": "...", "score": 0, "color": "..."}]

        # Ініціалізуємо карту України (ISO-коди SimpleMaps: UA05, UA32, UA46 і т.д.)
        self.map_state: Dict[str, Any] = {
            "UA05": {"owner_id": None, "name": "Вінницька"},
            "UA07": {"owner_id": None, "name": "Волинська"},
            "UA09": {"owner_id": None, "name": "Луганська"},
            "UA12": {"owner_id": None, "name": "Дніпропетровська"},
            "UA14": {"owner_id": None, "name": "Донецька"},
            "UA18": {"owner_id": None, "name": "Житомирська"},
            "UA21": {"owner_id": None, "name": "Закарпатська"},
            "UA23": {"owner_id": None, "name": "Запорізька"},
            "UA26": {"owner_id": None, "name": "Івано-Франківська"},
            "UA30": {"owner_id": None, "name": "Київська"},
            "UA32": {"owner_id": None, "name": "м. Київ"},
            "UA35": {"owner_id": None, "name": "Кіровоградська"},
            "UA40": {"owner_id": None, "name": "м. Севастополь"},
            "UA43": {"owner_id": None, "name": "АР Крим"},
            "UA46": {"owner_id": None, "name": "Львівська"},
            "UA48": {"owner_id": None, "name": "Миколаївська"},
            "UA51": {"owner_id": None, "name": "Одеська"},
            "UA53": {"owner_id": None, "name": "Полтавська"},
            "UA56": {"owner_id": None, "name": "Рівненська"},
            "UA59": {"owner_id": None, "name": "Сумська"},
            "UA61": {"owner_id": None, "name": "Тернопільська"},
            "UA63": {"owner_id": None, "name": "Харківська"},
            "UA65": {"owner_id": None, "name": "Херсонська"},
            "UA68": {"owner_id": None, "name": "Хмельницька"},
            "UA71": {"owner_id": None, "name": "Черкаська"},
            "UA74": {"owner_id": None, "name": "Чернігівська"},
            "UA77": {"owner_id": None, "name": "Чернівецька"},
        }

        self.current_answers: Dict[str, Any] = {}
        self.current_question: Optional[Dict[str, Any]] = None
        self.timer_task: Optional[asyncio.Task] = None
        self.timer_seconds: int = 0
        self.current_turn_player_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Перетворює стейт гри в чистий словник для відправки по WS"""
        return {
            "game_id": self.game_id,
            "status": self.status,
            "players": self.players,
            "map_state": self.map_state,
            "timer_seconds": self.timer_seconds,
            "current_question": self.current_question,
            "current_turn_player_id": self.current_turn_player_id
        }

    def advance_turn(self):
        """Передає хід наступному гравцю за списком"""
        if not self.players:
            return

        player_ids = [p["user_id"] for p in self.players]

        if self.current_turn_player_id in player_ids:
            current_idx = player_ids.index(self.current_turn_player_id)
            next_idx = (current_idx + 1) % len(player_ids)
            self.current_turn_player_id = player_ids[next_idx]
        else:
            self.current_turn_player_id = player_ids[0]

    def handle_claim_region(self, user_id: str, region_id: str):
        """Логіка захоплення області всередині конкретної сесії гри"""
        # 1. Перевірка статусу
        if self.status not in ["CLAIM_TERRITORY", "LOBBY"]:
            return {"error": "Зараз не фаза захоплення територій"}

        # 2. Перевіряємо хід
        if self.current_turn_player_id and self.current_turn_player_id != user_id:
            return {"error": "Зараз хід іншого гравця"}

        # Normalize ID (наприклад "UA-32" -> "UA32")
        clean_region_id = region_id.replace("-", "")

        # 3. Перевіряємо існування та чи територія вільна
        if clean_region_id not in self.map_state:
            self.map_state[clean_region_id] = {"owner_id": None}

        region = self.map_state[clean_region_id]
        if region.get("owner_id") is not None:
            return {"error": "Ця територія вже зайнята!"}

        # 4. Захоплюємо територію
        self.map_state[clean_region_id]["owner_id"] = user_id

        # Нараховуємо бали гравцю (+100 за кожну область)
        for player in self.players:
            if player["user_id"] == user_id:
                player["score"] += 100
                break

        # 5. ПЕРЕДАЄМО ХІД НАСТУПНОМУ ГРАВЦЮ! 🔄
        self.advance_turn()

        return {"status": "success", "region_id": clean_region_id, "owner_id": user_id}

class GameManager:
    def __init__(self):
        # Сховище активних сесій: { room_id: GameSession }
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

        # Призначаємо яскраві кольори для 3 гравців
        colors = ["#ef4444", "#3b82f6", "#22c55e"]  # Червоний, Синій, Зелений
        player_color = colors[len(game.players) % 3]

        game.players.append({
            "user_id": user_id,
            "username": username,
            "score": 0,
            "color": player_color
        })

        # За замовчуванням робимо першого гравця ходячим
        if not game.current_turn_player_id:
            game.current_turn_player_id = user_id

        # Якщо зібралося 2 або 3 гравці — можна стартувати фазу захоплення
        if len(game.players) >= 2 and game.status == "LOBBY":
            game.status = "CLAIM_TERRITORY"

        return game

    async def remove_player_from_game(self, room_id: str, user_id: str):
        if room_id in self.active_games:
            game = self.active_games[room_id]
            game.players = [p for p in game.players if p["user_id"] != user_id]

            if not game.players:
                if game.timer_task:
                    game.timer_task.cancel()
                del self.active_games[room_id]

    async def claim_region(self, room_id: str, user_id: str, region_id: str):
        """Викликається із сокету в game_ws.py"""
        game = self.active_games.get(room_id)
        if not game:
            return {"error": "Кімнату не знайдено"}

        # Викликаємо захоплення в сесії гри
        result = game.handle_claim_region(user_id, region_id)

        if "error" not in result:
            # Розсилаємо оновлений стан всім гравцям у кімнаті
            await manager.broadcast_to_room(room_id, {
                "action": "room_state",
                "data": game.to_dict()
            })

        return result

    async def submit_answer(self, room_id: str, user_id: str, answer: str):
        game = self.active_games.get(room_id)
        if not game or not game.current_question:
            return

        if user_id in game.current_answers:
            return

        game.current_answers[user_id] = {
            "answer": answer,
            "time_left": game.timer_seconds
        }

        if len(game.current_answers) == len(game.players):
            if game.timer_task:
                game.timer_task.cancel()
            await self.handle_round_timeout(room_id)

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
                points_gained = 100 + (user_ans["time_left"] * 10)
                player["score"] += points_gained

            results.append({
                "username": player["username"],
                "is_correct": is_correct,
                "points_gained": points_gained,
                "total_score": player["score"]
            })

        await manager.broadcast_to_room(room_id, {
            "action": "round_results",
            "data": {
                "correct_answer": correct,
                "results": results,
                "players": game.players
            }
        })


# Ініціалізуємо глобальний сервіс
game_manager = GameManager()