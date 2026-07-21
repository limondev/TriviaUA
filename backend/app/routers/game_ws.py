# app/routers/game_ws.py
import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from app.core.config import settings
from app.services.websocket_maps import manager
from app.services.game_manager import game_manager  # Імпортуємо менеджер ігор

router = APIRouter(tags=["Game WS"])


async def get_user_from_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        if user_id and username:
            return {"user_id": user_id, "username": username}
    except jwt.PyJWTError as e:
        print(f"Помилка JWT токену: {e}")
        pass
    return None


@router.websocket("/ws/game/{room_id}")
async def websocket_game_endpoint(websocket: WebSocket, room_id: str, token: str = Query(...)):
    user_data = await get_user_from_token(token)
    if not user_data:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = user_data["user_id"]
    username = user_data["username"]

    # 1. Підключаємо сокет до транслятора
    await manager.connect(room_id, user_id, websocket)

    # 2. Реєструємо гравця в бізнес-стейті гри
    game_state = await game_manager.add_player_to_game(room_id, user_id, username)

    # Відправляємо особисто цьому гравцю поточний стейт кімнати відразу при вході
    await websocket.send_json({
        "action": "room_state",
        "data": game_state.to_dict()
    })

    try:
        while True:
            data = await websocket.receive_json()

            action = data.get("action")
            payload = data.get("data", {})

            if action == "submit_answer":
                answer = payload.get("answer")
                if answer is not None:
                    await game_manager.submit_answer(room_id, user_id, str(answer))

    except WebSocketDisconnect:
        # Обробка виходу / дисконекту
        await manager.disconnect(room_id, user_id)
        await game_manager.remove_player_from_game(room_id, user_id)

        await manager.broadcast_to_room(room_id, {
            "action": "player_left",
            "data": {"username": username, "message": f"Гравець {username} залишив гру."}
        })