from pydantic import BaseModel
from typing import Optional, Any, Dict, List

# Що ми відправляємо гравцям (Базовий івент)
class GameEventOut(BaseModel):
    action: str  # наприклад: "room_updated", "game_started", "timer_tick", "error"
    data: Any    # будь-які корисні дані (наприклад, актуальний GameState)

# Базова схема гравця для стейту
class PlayerState(BaseModel):
    user_id: str
    username: str
    score: int = 0
    is_online: bool = True

# Повний стейт гри, який буде постійно «летіти» на фронтенд
class GameStateSchema(BaseModel):
    game_id: str
    status: str  # "LOBBY", "PHASE_1_CAPTURE", "PHASE_2_DUEL", "FINISHED"
    players: List[PlayerState]
    map_state: Dict[str, Any]  # ID області -> Хто володіє
    current_turn_player_id: Optional[str] = None
    timer_seconds: int = 0