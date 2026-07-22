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

    # 1. Підключаємо сокет до транслятора кімнати
    await manager.connect(room_id, user_id, websocket)

    # 2. Реєструємо гравця в бізнес-стейті гри
    game_state = await game_manager.add_player_to_game(room_id, user_id, username)

    game_state.status = "CLAIM_TERRITORY" #тест, потім прибрати
    # 3. ФІКС: БРОДКАСТИМО ОНОВЛЕНИЙ СТАН ВСІМ ГРАВЦЯМ КІМНАТИ
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
                    result = await game_manager.claim_region(room_id, user_id, region_id)
                    if isinstance(result, dict) and "error" in result:
                        await websocket.send_json({
                            "action": "error",
                            "data": {"message": result["error"]}
                        })

    except WebSocketDisconnect:
        # Обробка виходу / дисконекту
        await manager.disconnect(room_id, user_id)
        await game_manager.remove_player_from_game(room_id, user_id)

        # При виході також розсилаємо оновлений стан або повідомлення
        await manager.broadcast_to_room(room_id, {
            "action": "player_left",
            "data": {"username": username, "message": f"Гравець {username} залишив гру."}
        })