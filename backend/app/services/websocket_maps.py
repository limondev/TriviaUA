from fastapi import WebSocket
from typing import Dict, Set
import json


class ConnectionManager:
    def __init__(self):
        # Структура: { room_id: { user_id: WebSocket } }
        self.active_rooms: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, room_id: str, user_id: str, websocket: WebSocket):
        await websocket.accept()

        # Якщо такої кімнати ще немає в пам'яті — створюємо
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = {}

        # Зберігаємо сокет користувача в цій кімнаті
        self.active_rooms[room_id][user_id] = websocket

    async def disconnect(self, room_id: str, user_id: str):
        if room_id in self.active_rooms:
            if user_id in self.active_rooms[room_id]:
                del self.active_rooms[room_id][user_id]

            # Якщо в кімнаті не залишилось людей — видаляємо саму кімнату з пам'яті
            if not self.active_rooms[room_id]:
                del self.active_rooms[room_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Відправити повідомлення конкретному сокету"""
        await websocket.send_json(message)

    async def broadcast_to_room(self, room_id: str, message: dict):
        """Відправити повідомлення ВСІМ учасникам конкретної кімнати"""
        if room_id in self.active_rooms:
            # Створюємо копію списку сокетів, щоб уникнути RuntimeError під час ітерації
            active_sockets = list(self.active_rooms[room_id].items())

            for user_id, websocket in active_sockets:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    print(f"Помилка відправки сокету {user_id}: {e}")
                    # Безпечно видаляємо мертвий сокет
                    await self.disconnect(room_id, user_id)


# Створюємо єдиний екземпляр менеджера для всього додатка
manager = ConnectionManager()