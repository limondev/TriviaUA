import asyncio
import random
from typing import Dict, List, Any, Optional
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.all_models import Question
from app.services.websocket_maps import manager

REGION_NAMES = {
            "UA05": "Вінницька область", "UA07": "Волинська область", "UA09": "Луганська область",
            "UA12": "Дніпропетровська область", "UA14": "Донецька область", "UA18": "Житомирська область",
            "UA21": "Закарпатська область", "UA23": "Запорізька область", "UA26": "Івано-Франківська область",
            "UA30": "Київська область", "UA32": "м. Київ", "UA35": "Кіровоградська область",
            "UA40": "м. Севастополь", "UA43": "АР Крим", "UA46": "Львівська область",
            "UA48": "Миколаївська область", "UA51": "Одеська область", "UA53": "Полтавська область",
            "UA56": "Рівненська область", "UA59": "Сумська область", "UA61": "Тернопільська область",
            "UA63": "Харківська область", "UA65": "Херсонська область", "UA68": "Хмельницька область",
            "UA71": "Черкаська область", "UA74": "Чернігівська область", "UA77": "Чернівецька область"
        }

class GameSession:
    def __init__(self, game_id: str):
        self.game_id: str = game_id
        # Стани: LOBBY, CAPITAL_SELECTION, CLAIM_TERRITORY, PHASE_2_DUEL, QUESTION, FINISHED
        self.status: str = "LOBBY"
        self.players: List[Dict[str, Any]] = []

        self.map_state: Dict[str, Any] = {
            "UA05": {"owner_id": None, "is_capital": False},
            "UA07": {"owner_id": None, "is_capital": False},
            "UA09": {"owner_id": None, "is_capital": False},
            "UA12": {"owner_id": None, "is_capital": False},
            "UA14": {"owner_id": None, "is_capital": False},
            "UA18": {"owner_id": None, "is_capital": False},
            "UA21": {"owner_id": None, "is_capital": False},
            "UA23": {"owner_id": None, "is_capital": False},
            "UA26": {"owner_id": None, "is_capital": False},
            "UA30": {"owner_id": None, "is_capital": False},
            "UA32": {"owner_id": None, "is_capital": False},
            "UA35": {"owner_id": None, "is_capital": False},
            "UA40": {"owner_id": None, "is_capital": False},
            "UA43": {"owner_id": None, "is_capital": False},
            "UA46": {"owner_id": None, "is_capital": False},
            "UA48": {"owner_id": None, "is_capital": False},
            "UA51": {"owner_id": None, "is_capital": False},
            "UA53": {"owner_id": None, "is_capital": False},
            "UA56": {"owner_id": None, "is_capital": False},
            "UA59": {"owner_id": None, "is_capital": False},
            "UA61": {"owner_id": None, "is_capital": False},
            "UA63": {"owner_id": None, "is_capital": False},
            "UA65": {"owner_id": None, "is_capital": False},
            "UA68": {"owner_id": None, "is_capital": False},
            "UA71": {"owner_id": None, "is_capital": False},
            "UA74": {"owner_id": None, "is_capital": False},
            "UA77": {"owner_id": None, "is_capital": False},

        }

        self.current_answers: Dict[str, Any] = {}
        self.current_question: Optional[Dict[str, Any]] = None
        self.timer_task: Optional[asyncio.Task] = None
        self.timer_seconds: int = 0
        self.current_turn_player_id: Optional[str] = None
        self.duel_target_region: Optional[str] = None
        self.defender_id: Optional[str] = None
        self.last_notification: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "game_id": self.game_id,
            "status": self.status,
            "players": self.players,
            "map_state": self.map_state,
            "timer_seconds": self.timer_seconds,
            "current_question": self.current_question,
            "current_turn_player_id": self.current_turn_player_id,
            "duel_target_region": self.duel_target_region,
            "last_notification": self.last_notification
        }

    def auto_fill_map(self):
        """Рандомно заповнює мапу та призначає першу область кожного гравця Замком 🏰"""
        if not self.players:
            return

        free_regions = [r for r, d in self.map_state.items() if d["owner_id"] is None]
        random.shuffle(free_regions)

        # Словник для відстеження, чи отримав гравець свій Замок
        capitals_assigned = {p["user_id"]: False for p in self.players}

        for i, reg in enumerate(free_regions):
            player = self.players[i % len(self.players)]
            p_id = player["user_id"]

            self.map_state[reg]["owner_id"] = p_id
            player["score"] += 100

            # Перша видана область стає Замком (Столицею) гравця!
            if not capitals_assigned[p_id]:
                self.map_state[reg]["is_capital"] = True
                capitals_assigned[p_id] = True
            else:
                self.map_state[reg]["is_capital"] = False

        self.status = "PHASE_2_DUEL"


class GameManager:
    def __init__(self):
        self.active_games: Dict[str, GameSession] = {}

    def get_or_create_game(self, room_id: str) -> GameSession:
        if room_id not in self.active_games:
            self.active_games[room_id] = GameSession(room_id)
        return self.active_games[room_id]

    async def add_player_to_game(self, room_id: str, user_id: str, username: str):
        game = self.get_or_create_game(room_id)

        if any(p["user_id"] == user_id for p in game.players):
            return game

        colors = ["#ef4444", "#3b82f6", "#22c55e"]
        player_color = colors[len(game.players) % 3]

        game.players.append({
            "user_id": user_id,
            "username": username,
            "score": 0,
            "color": player_color
        })

        if not game.current_turn_player_id:
            game.current_turn_player_id = user_id

        if len(game.players) >= 2 and game.status == "LOBBY":
            game.status = "CAPITAL_SELECTION"

        return game

    async def auto_fill_and_start_duels(self, room_id: str):
        """Авто-заповнення мапи для швидкого тесту дуелей"""
        game = self.active_games.get(room_id)
        if game:
            if game.timer_task:
                game.timer_task.cancel()

            game.auto_fill_map()

            await manager.broadcast_to_room(room_id, {
                "action": "room_state",
                "data": game.to_dict()
            })
            # Запускаємо таймер вибору ходу в дуелях
            await self.start_turn_timer(room_id)

    async def handle_click_region(self, room_id: str, user_id: str, region_id: str):
        game = self.active_games.get(room_id)
        if not game:
            return {"error": "Кімнату не знайдено"}

        clean_id = region_id.replace("-", "")

        # 1. АТАКА В ДУЕЛЯХ (PHASE_2_DUEL)
        if game.status == "PHASE_2_DUEL":
            if game.current_turn_player_id != user_id:
                return {"error": "Зараз не твій хід для атаки!"}

            region = game.map_state.get(clean_id)
            if not region or region.get("owner_id") == user_id:
                return {"error": "Не можна атакувати власну область!"}

            # Зупиняємо таймер вибору атаки
            if game.timer_task:
                game.timer_task.cancel()

            game.duel_target_region = clean_id
            game.defender_id = region["owner_id"]
            game.status = "QUESTION"

            await self.start_duel_question(room_id)
            return {"status": "attack_started"}

        # 2. КЛІК В ЗАХОПЛЕННІ / ВИБОРІ СТОЛИЦІ
        elif game.status in ["CAPITAL_SELECTION", "CLAIM_TERRITORY"]:
            if game.map_state.get(clean_id, {}).get("owner_id") is None:
                if game.timer_task:
                    game.timer_task.cancel()

                game.map_state[clean_id]["owner_id"] = user_id
                if game.status == "CAPITAL_SELECTION":
                    game.map_state[clean_id]["is_capital"] = True

                for p in game.players:
                    if p["user_id"] == user_id:
                        p["score"] += 100

                # Ротація ходу
                p_ids = [p["user_id"] for p in game.players]
                curr_idx = p_ids.index(user_id)
                game.current_turn_player_id = p_ids[(curr_idx + 1) % len(p_ids)]

                await manager.broadcast_to_room(room_id, {
                    "action": "room_state",
                    "data": game.to_dict()
                })
                await self.start_turn_timer(room_id)

        return {"status": "ok"}

    async def start_turn_timer(self, room_id: str, seconds: int = 15):
        """Таймер на вибір області або вибір атаки"""
        game = self.active_games.get(room_id)
        if not game:
            return

        if game.timer_task:
            game.timer_task.cancel()

        game.timer_seconds = seconds
        game.timer_task = asyncio.create_task(self._turn_timer_loop(room_id))

    async def _turn_timer_loop(self, room_id: str):
        game = self.active_games.get(room_id)
        if not game:
            return

        try:
            while game.timer_seconds > 0:
                await manager.broadcast_to_room(room_id, {
                    "action": "room_state",
                    "data": game.to_dict()
                })
                await asyncio.sleep(1)
                game.timer_seconds -= 1

            await self.handle_turn_timeout(room_id)

        except asyncio.CancelledError:
            pass

    async def handle_turn_timeout(self, room_id: str):
        """Якщо гравець провів 15 секунд і не зробив хід"""
        game = self.active_games.get(room_id)
        if not game:
            return

        p_ids = [p["user_id"] for p in game.players]
        if game.current_turn_player_id in p_ids:
            curr_idx = p_ids.index(game.current_turn_player_id)
            game.current_turn_player_id = p_ids[(curr_idx + 1) % len(p_ids)]

        await manager.broadcast_to_room(room_id, {
            "action": "room_state",
            "data": game.to_dict()
        })

        if game.status in ["CLAIM_TERRITORY", "PHASE_2_DUEL", "CAPITAL_SELECTION"]:
            await self.start_turn_timer(room_id)

    async def start_duel_question(self, room_id: str):
        game = self.active_games.get(room_id)
        if not game:
            return

        game.current_answers = {}

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Question).order_by(Question.id))
            questions = result.scalars().all()
            if questions:
                q = random.choice(questions)
                game.current_question = {
                    "id": q.id,
                    "type": q.type,
                    "text": q.text,
                    "options": q.options,
                    "correct_answer": str(q.correct_answer) if q.correct_answer else "603700"
                }
            else:
                game.current_question = {
                    "id": 1,
                    "type": "NUMBER",
                    "text": "Яка офіційна площа території України у км²?",
                    "options": None,
                    "correct_answer": "603700"
                }

        game.timer_seconds = 15

        if game.timer_task:
            game.timer_task.cancel()

        game.timer_task = asyncio.create_task(self._question_timer_loop(room_id))

    async def _question_timer_loop(self, room_id: str):
        """Таймер для відліку 15 секунд під час теми питання"""
        game = self.active_games.get(room_id)
        if not game:
            return

        try:
            while game.timer_seconds > 0:
                await manager.broadcast_to_room(room_id, {
                    "action": "room_state",
                    "data": game.to_dict()
                })
                await asyncio.sleep(1)
                game.timer_seconds -= 1

            await self.handle_round_timeout(room_id)

        except asyncio.CancelledError:
            pass

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

        # Якщо всі відповіли — достроково завершуємо таймер
        if len(game.current_answers) == len(game.players):
            if game.timer_task:
                game.timer_task.cancel()
            await self.handle_round_timeout(room_id)

    async def handle_round_timeout(self, room_id: str):
        game = self.active_games.get(room_id)
        if not game or not game.current_question:
            return

        correct_str = str(game.current_question.get("correct_answer", "")).strip()
        winner_id = None
        winner_name = None

        # 1. Визначаємо переможця
        if game.current_question.get("type") == "NUMBER":
            try:
                target = float(correct_str)
                best_diff = float("inf")

                for u_id, ans_data in game.current_answers.items():
                    val = float(ans_data.get("answer", 0))
                    diff = abs(target - val)
                    if diff < best_diff:
                        best_diff = diff
                        winner_id = u_id
            except (ValueError, TypeError):
                pass
        else:
            for u_id, ans_data in game.current_answers.items():
                if str(ans_data.get("answer", "")).strip().upper() == correct_str.upper():
                    winner_id = u_id
                    break

        if winner_id:
            for p in game.players:
                if p["user_id"] == winner_id:
                    winner_name = p["username"]
                    break

        target_reg = game.duel_target_region or ""
        region_name = REGION_NAMES.get(target_reg, "Територія")

        # 2. Передача території та Захист/Захоплення Столиці (Замку)
        if winner_id and target_reg in game.map_state:
            old_owner_id = game.map_state[target_reg].get("owner_id")
            is_capital = game.map_state[target_reg].get("is_capital", False)

            # Переписуємо область на переможця
            game.map_state[target_reg]["owner_id"] = winner_id

            for p in game.players:
                if p["user_id"] == winner_id:
                    p["score"] += 200

            # 🏰 ЯКЩО ЦЕ БУВ ЗАМОК (СТОЛИЦЯ) 🏰
            if is_capital and old_owner_id and old_owner_id != winner_id:
                # Всі інші території програвшого гравця також переходять переможцю!
                for reg_id, reg_data in game.map_state.items():
                    if reg_data.get("owner_id") == old_owner_id:
                        reg_data["owner_id"] = winner_id

                # Шукаємо ім'я програвшого
                loser_name = next((p["username"] for p in game.players if p["user_id"] == old_owner_id), "Супротивник")
                game.last_notification = f"👑 {winner_name} захопив Замок {loser_name} і забрав усі його землі!"
            else:
                game.last_notification = f"⚔️ {region_name} перейшла під контроль {winner_name}!"
        else:
            game.last_notification = f"🛡️ Атаку на {region_name} було відбито!"

        # 3. ПЕРЕВІРКА НА GAME OVER 🏁
        # Рахуємо, скільки гравців володіють хоча б однією областю
        active_owners = set(d["owner_id"] for d in game.map_state.values() if d.get("owner_id") is not None)

        if len(active_owners) == 1:
            # Лишився 1 володар усієї картографії — Кінець Гри!
            game.status = "FINISHED"
            winner_user_id = list(active_owners)[0]
            champ_name = next((p["username"] for p in game.players if p["user_id"] == winner_user_id), "Гравець")
            game.last_notification = f"🏆 ГРУ ЗАВЕРШЕНО! Переможець: {champ_name}!"
        else:
            # Ротація ходу
            p_ids = [p["user_id"] for p in game.players]
            if game.current_turn_player_id in p_ids:
                curr_idx = p_ids.index(game.current_turn_player_id)
                game.current_turn_player_id = p_ids[(curr_idx + 1) % len(p_ids)]

            game.status = "PHASE_2_DUEL"

        game.current_question = None
        game.duel_target_region = None
        game.defender_id = None

        # 4. Бродкастимо стан
        await manager.broadcast_to_room(room_id, {
            "action": "room_state",
            "data": game.to_dict()
        })

        if game.status != "FINISHED":
            await self.start_turn_timer(room_id)
        else:
            asyncio.create_task(self._clear_notification_after_delay(room_id, 8))

    async def _clear_notification_after_delay(self, room_id: str, delay: int):
        """Очищає last_notification через задану кількість секунд"""
        await asyncio.sleep(delay)
        game = self.active_games.get(room_id)
        if game and game.last_notification:
            game.last_notification = None
            # Бродкастимо оновлений стан без сповіщення
            await manager.broadcast_to_room(room_id, {
                "action": "room_state",
                "data": game.to_dict()
            })

game_manager = GameManager()