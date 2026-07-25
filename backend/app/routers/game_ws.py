# app/routers/game_ws.py
import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from app.core.config import settings
from app.services.websocket_maps import manager
from app.services.game_manager import game_manager

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

    # 1. СПОЧАТКУ додаємо сокет у WS-менеджер
    await manager.connect(room_id, user_id, websocket)

    # 2. ПОТІМ додаємо гравця у стейт гри
    game_state = await game_manager.add_player_to_game(room_id, user_id, username)

    # 3. Розсилаємо оновлений стейт УСІМ активним сокетам кімнати
    await manager.broadcast_to_room(room_id, {
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

            elif action == "claim_region":
                region_id = payload.get("region_id")
                if region_id:
                    await game_manager.handle_click_region(room_id, user_id, region_id)

            elif action == "auto_fill":
                await game_manager.auto_fill_and_start_duels(room_id)

    except WebSocketDisconnect:
        await manager.disconnect(room_id, user_id)
        await game_manager.remove_player_from_game(room_id, user_id)

        await manager.broadcast_to_room(room_id, {
            "action": "player_left",
            "data": {"username": username, "message": f"Гравець {username} залишив гру."}
        })