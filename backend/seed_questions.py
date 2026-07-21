# backend/seed_questions.py
import asyncio
from sqlalchemy.future import select
from app.core.database import AsyncSessionLocal, engine
from app.models.all_models import Question

QUESTIONS_DATA = [
    # --- ТИП NUMBER (Вгадай число) ---
    {
        "type": "NUMBER",
        "text": "В який рік почалося велике козацьке повстання під проводом Богдана Хмельницького?",
        "options": None,
        "correct_answer": "1648"
    },
    {
        "type": "NUMBER",
        "text": "Яка офіційна площа території України (разом із тимчасово окупованими територіями) у квадратних кілометрах?",
        "options": None,
        "correct_answer": "603548"
    },
    {
        "type": "NUMBER",
        "text": "Скільки кілометрів становить максимальна дальльність польоту українського далекобійного дрона-ракети «Паляниця» (за відкритими даними)?",
        "options": None,
        "correct_answer": "700"
    },
    {
        "type": "NUMBER",
        "text": "У якому році відбулося Хрещення Русі князем Володимиром Великим?",
        "options": None,
        "correct_answer": "988"
    },
    {
        "type": "NUMBER",
        "text": "У якому році український гурт Kalush Orchestra здобув перемогу на пісенному конкурсі Євробачення з піснею 'Stefania'?",
        "options": None,
        "correct_answer": "2022"
    },
    {
        "type": "NUMBER",
        "text": "Яка висота найвищої точки України — гори Говерла (в метрах)?",
        "options": None,
        "correct_answer": "2061"
    },

    # --- ТИП CHOICE (4 Варіанти) ---
    {
        "type": "CHOICE",
        "text": "Як називається відомий український морський безпілотник, який успішно вражав кораблі Чорноморського флоту РФ?",
        "options": {"A": "Sea Baby", "B": "Bayraktar", "C": "Shark", "D": "Стриж"},
        "correct_answer": "A"
    },
    {
        "type": "CHOICE",
        "text": "Яку назву має український розвідувальний БПЛА, призначений для коригування артилерії та розвідки, що має характерний крилоподібний силует?",
        "options": {"A": "Посейдон", "B": "Shark", "C": "Лелека-100", "D": "Фурія"},
        "correct_answer": "B"
    },
    {
        "type": "CHOICE",
        "text": "Як називався головний військово-політичний орган управління у Запорозькій Січі, де козаки приймали найважливіші рішення?",
        "options": {"A": "Генеральна Рада", "B": "Козацька Рада", "C": "Директорія", "D": "Гетьманат"},
        "correct_answer": "B"
    },
    {
        "type": "CHOICE",
        "text": "Яка річка є найдовшою серед тих, що протікають виключно територією України (від витоку до гирла)?",
        "options": {"A": "Дніпро", "B": "Південний Буг", "C": "Дністер", "D": "Десна"},
        "correct_answer": "B"
    },
    {
        "type": "CHOICE",
        "text": "Хто є автором першої Конституції Пилипа Орлика, яка була написана в 1710 році?",
        "options": {"A": "Іван Мазепа", "B": "Пилип Орлик", "C": "Богдан Хмельницький", "D": "Павло Скоропадський"},
        "correct_answer": "B"
    },
    {
        "type": "CHOICE",
        "text": "На якій грошовій купюрі України зображено видатного філософа Григорія Сковороду?",
        "options": {"A": "100 гривень", "B": "200 гривень", "C": "500 гривень", "D": "1000 гривень"},
        "correct_answer": "C"
    }
]


async def seed_questions():
    print("Запуск сидингу питань...")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Question))
        existing_count = len(result.scalars().all())

        if existing_count > 0:
            print(print(f"База даних вже містить {existing_count} питань. Сидинг скасовано."))
            return

        # Додаємо наші питання
        for q_data in QUESTIONS_DATA:
            question = Question(
                type=q_data["type"],
                text=q_data["text"],
                options=q_data["options"],
                correct_answer=q_data["correct_answer"]
            )
            session.add(question)

        await session.commit()
        print(f"Успішно додано {len(QUESTIONS_DATA)} питань до бази даних!")


if __name__ == "__main__":
    asyncio.run(seed_questions())